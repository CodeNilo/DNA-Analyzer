"""
Pruebas unitarias para serializers.py

Cubre:
- DNASequenceSerializer
- DNASequenceUploadSerializer
- Parsing de diferentes formatos (CSV, FASTA, TXT)
- Validaciones de archivo
- Detección de duplicados
"""

import io
from django.test import TestCase
from rest_framework.serializers import ValidationError

from sequences_api.models import DNASequence
from sequences_api.serializers import (
    DNASequenceSerializer,
    DNASequenceUploadSerializer
)


class DNASequenceSerializerTests(TestCase):
    """Pruebas para DNASequenceSerializer"""

    def setUp(self):
        self.sequence = DNASequence.objects.create(
            name="test_sequence",
            sequence="ATCGATCG"
        )

    def test_serializes_correctly(self):
        """Debe serializar correctamente todos los campos"""
        serializer = DNASequenceSerializer(self.sequence)
        data = serializer.data

        self.assertEqual(data['name'], "test_sequence")
        self.assertEqual(data['length'], 8)
        self.assertEqual(data['gc_content'], 50.0)
        self.assertIn('id', data)
        self.assertIn('uploaded_at', data)

    def test_excludes_sequence_field(self):
        """No debe incluir el campo sequence (por privacidad/tamaño)"""
        serializer = DNASequenceSerializer(self.sequence)
        self.assertNotIn('sequence', serializer.data)

    def test_gc_content_calculation(self):
        """Debe calcular gc_content correctamente vía SerializerMethodField"""
        seq_100 = DNASequence.objects.create(name="all_gc", sequence="GGCC")
        serializer = DNASequenceSerializer(seq_100)
        self.assertEqual(serializer.data['gc_content'], 100.0)

    def test_gc_content_when_null(self):
        """Debe calcular gc_content si es None"""
        seq = DNASequence(name="test", sequence="ATCG")
        seq.gc_content = None
        seq.save()

        serializer = DNASequenceSerializer(seq)
        self.assertEqual(serializer.data['gc_content'], 50.0)


class DNASequenceUploadSerializerTests(TestCase):
    """Pruebas para DNASequenceUploadSerializer"""

    def create_mock_file(self, content, filename="test.txt"):
        """Helper para crear archivos mock"""
        file_obj = io.BytesIO(content.encode('utf-8'))
        file_obj.name = filename
        file_obj.size = len(content.encode('utf-8'))
        return file_obj

    def test_upload_simple_text_file(self):
        """Debe cargar archivo de texto simple"""
        content = "ATCGATCG"
        file_obj = self.create_mock_file(content)

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        self.assertTrue(serializer.is_valid())

        instance = serializer.save()
        self.assertEqual(instance.sequence, "ATCGATCG")
        self.assertEqual(instance.length, 8)

    def test_upload_fasta_format(self):
        """Debe parsear formato FASTA correctamente"""
        content = ">sequence_1\nATCG\nATCG"
        file_obj = self.create_mock_file(content)

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        self.assertTrue(serializer.is_valid())

        instance = serializer.save()
        self.assertEqual(instance.sequence, "ATCGATCG")

    def test_upload_fasta_multiple_headers(self):
        """Debe ignorar múltiples encabezados FASTA"""
        content = ">seq1\nATCG\n>seq2\nATCG"
        file_obj = self.create_mock_file(content)

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        self.assertTrue(serializer.is_valid())

        instance = serializer.save()
        self.assertEqual(instance.sequence, "ATCGATCG")

    def test_upload_csv_with_commas(self):
        """Debe eliminar comas de CSV"""
        content = "A,T,C,G,A,T,C,G"
        file_obj = self.create_mock_file(content)

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        self.assertTrue(serializer.is_valid())

        instance = serializer.save()
        self.assertEqual(instance.sequence, "ATCGATCG")

    def test_upload_with_whitespace(self):
        """Debe manejar espacios y saltos de línea"""
        content = "AT CG\nAA TT"
        file_obj = self.create_mock_file(content)

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        self.assertTrue(serializer.is_valid())

        instance = serializer.save()
        self.assertEqual(instance.sequence, "ATCGAATT")

    def test_upload_with_custom_name(self):
        """Debe usar nombre personalizado si se provee"""
        content = "ATCG"
        file_obj = self.create_mock_file(content)

        serializer = DNASequenceUploadSerializer(data={
            'file': file_obj,
            'name': 'custom_name'
        })
        self.assertTrue(serializer.is_valid())

        instance = serializer.save()
        self.assertEqual(instance.name, 'custom_name')

    def test_upload_uses_filename_by_default(self):
        """Debe usar nombre del archivo si no se provee nombre"""
        content = "ATCG"
        file_obj = self.create_mock_file(content, filename="my_sequence.txt")

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        self.assertTrue(serializer.is_valid())

        instance = serializer.save()
        self.assertEqual(instance.name, 'my_sequence.txt')

    def test_validates_file_size_limit(self):
        """Debe rechazar archivos que excedan 150MB"""
        # Crear archivo mock con tamaño > 150MB
        content = "A" * 100
        file_obj = self.create_mock_file(content)
        file_obj.size = 160 * 1024 * 1024  # 160MB

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)

    def test_detects_duplicate_by_hash(self):
        """Debe detectar duplicados por hash y no crear nuevo"""
        # Crear primera secuencia
        content = "ATCG"
        file_obj1 = self.create_mock_file(content)

        serializer1 = DNASequenceUploadSerializer(data={'file': file_obj1})
        serializer1.is_valid()
        instance1 = serializer1.save()

        # Intentar subir la misma secuencia
        file_obj2 = self.create_mock_file(content)
        serializer2 = DNASequenceUploadSerializer(data={'file': file_obj2})
        serializer2.is_valid()
        instance2 = serializer2.save()

        # Debe devolver la misma instancia
        self.assertEqual(instance1.id, instance2.id)
        self.assertFalse(serializer2.was_created)

    def test_marks_was_created_flag(self):
        """Debe marcar was_created=True para nuevas secuencias"""
        content = "ATCGATCGATCG"
        file_obj = self.create_mock_file(content)

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        serializer.is_valid()
        serializer.save()

        self.assertTrue(serializer.was_created)

    def test_invalid_dna_characters(self):
        """Debe rechazar caracteres inválidos"""
        content = "ATCG123XYZ"
        file_obj = self.create_mock_file(content)

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
            serializer.save()

    def test_empty_file(self):
        """Debe rechazar archivo vacío"""
        content = ""
        file_obj = self.create_mock_file(content)

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
            serializer.save()

    def test_file_required(self):
        """Campo file es requerido"""
        serializer = DNASequenceUploadSerializer(data={})
        self.assertFalse(serializer.is_valid())
        self.assertIn('file', serializer.errors)

    def test_lowercase_normalized_to_uppercase(self):
        """Debe normalizar minúsculas a mayúsculas"""
        content = "atcg"
        file_obj = self.create_mock_file(content)

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        serializer.is_valid()
        instance = serializer.save()

        self.assertEqual(instance.sequence, "ATCG")

    def test_sequence_with_n(self):
        """Debe aceptar secuencias con N"""
        content = "ATCGNATCG"
        file_obj = self.create_mock_file(content)

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        self.assertTrue(serializer.is_valid())

        instance = serializer.save()
        self.assertEqual(instance.sequence, "ATCGNATCG")


class ParseSequenceMethodTests(TestCase):
    """Pruebas para el método _parse_sequence"""

    def test_parse_with_sequence_column_csv(self):
        """Debe parsear CSV con columna específica"""
        content = "name,sequence,other\nseq1,ATCG,data\nseq2,ATCG,data"
        file_obj = io.BytesIO(content.encode('utf-8'))
        file_obj.name = "test.csv"
        file_obj.size = len(content)

        serializer = DNASequenceUploadSerializer(data={
            'file': file_obj,
            'sequence_column': 'sequence'
        })
        serializer.is_valid()
        instance = serializer.save()

        # Debe concatenar las secuencias de la columna
        self.assertEqual(instance.sequence, "ATCGATCG")

    def test_parse_multiline_sequence(self):
        """Debe manejar secuencias en múltiples líneas"""
        content = "ATCG\nATCG\nATCG"
        file_obj = io.BytesIO(content.encode('utf-8'))
        file_obj.name = "test.txt"
        file_obj.size = len(content)

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        serializer.is_valid()
        instance = serializer.save()

        self.assertEqual(instance.sequence, "ATCGATCGATCG")
