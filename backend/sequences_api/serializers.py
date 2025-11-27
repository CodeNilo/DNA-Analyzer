import csv
import hashlib
import io
from django.utils import timezone
from rest_framework import serializers

from .models import DNASequence
from .validators import normalize_sequence, validate_dna_sequence


class DNASequenceSerializer(serializers.ModelSerializer):
    gc_content = serializers.SerializerMethodField()

    def get_gc_content(self, obj):
        if obj.gc_content is not None:
            return obj.gc_content
        if obj.length:
            gc = sum(1 for c in obj.sequence if c in ('G', 'C'))
            return (gc / obj.length) * 100
        return 0.0

    class Meta:
        model = DNASequence
        fields = ['id', 'name', 'length', 'gc_content', 'uploaded_at']


class DNASequenceUploadSerializer(serializers.Serializer):
    file = serializers.FileField(write_only=True)
    name = serializers.CharField(required=False, allow_blank=True)
    sequence_column = serializers.CharField(required=False, allow_blank=True)

    def _parse_sequence(self, raw_text: str, sequence_column: str | None = None) -> str:
        """
        Intenta soportar CSV/FASTA/txt básicos:
        - Ignora líneas de encabezado FASTA (empiezan con '>')
        - Elimina comas y espacios
        Si se especifica sequence_column, usa DictReader y toma esa columna.
        """
        if sequence_column:
            reader = csv.DictReader(io.StringIO(raw_text))
            seq_chunks = []
            for row in reader:
                val = row.get(sequence_column, '')
                seq_chunks.append(str(val))
            cleaned = ''.join(seq_chunks)
            normalized = normalize_sequence(cleaned)
            return validate_dna_sequence(normalized)

        # Fallback texto plano/FASTA/CSV simple (una secuencia)
        lines = []
        for line in raw_text.splitlines():
            if line.startswith('>'):
                continue
            # Eliminamos comas y espacios intermedios
            lines.append(line.replace(',', ''))
        cleaned = ''.join(lines)
        normalized = normalize_sequence(cleaned)
        return validate_dna_sequence(normalized)

    def validate_file(self, file):
        max_size_bytes = 150 * 1024 * 1024  # 150MB
        if file.size > max_size_bytes:
            raise serializers.ValidationError("El archivo excede el límite de 150MB para esta versión.")
        return file

    def create(self, validated_data):
        file = validated_data['file']
        provided_name = validated_data.get('name')
        seq_column = validated_data.get('sequence_column') or None
        content = file.read()
        file_hash = hashlib.sha256(content).hexdigest()

        # Evitar duplicados: si ya existe, devolvemos la instancia
        existing = DNASequence.objects.filter(file_hash=file_hash).first()
        if existing:
            self.was_created = False
            return existing

        raw_text = content.decode('utf-8', errors='ignore')
        sequence = self._parse_sequence(raw_text, seq_column)

        name = provided_name or getattr(file, 'name', 'dna_sequence')
        instance = DNASequence.objects.create(
            name=name,
            sequence=sequence,
            length=len(sequence),
            uploaded_at=timezone.now(),
            file_hash=file_hash,
        )
        self.was_created = True
        return instance
