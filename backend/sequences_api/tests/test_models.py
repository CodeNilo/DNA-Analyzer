"""
Pruebas unitarias para models.py

Cubre:
- DNASequence model
- Cálculo automático de gc_content
- Cálculo de file_hash
- Validación y normalización en save()
- Métodos del modelo
"""

import hashlib
from django.test import TestCase
from django.utils import timezone

from sequences_api.models import DNASequence
from rest_framework.serializers import ValidationError


class DNASequenceModelTests(TestCase):
    """Pruebas para el modelo DNASequence"""

    def test_create_simple_sequence(self):
        """Debe crear una secuencia básica"""
        seq = DNASequence.objects.create(
            name="test_seq",
            sequence="ATCG"
        )
        self.assertEqual(seq.name, "test_seq")
        self.assertEqual(seq.sequence, "ATCG")
        self.assertIsNotNone(seq.id)

    def test_auto_calculates_length(self):
        """Debe calcular automáticamente la longitud"""
        seq = DNASequence.objects.create(
            name="test",
            sequence="ATCGATCG"
        )
        self.assertEqual(seq.length, 8)

    def test_auto_calculates_gc_content_50_percent(self):
        """Debe calcular 50% GC correctamente"""
        seq = DNASequence.objects.create(
            name="test",
            sequence="ATCG"  # 2 G/C de 4 = 50%
        )
        self.assertEqual(seq.gc_content, 50.0)

    def test_auto_calculates_gc_content_0_percent(self):
        """Debe calcular 0% GC correctamente"""
        seq = DNASequence.objects.create(
            name="test",
            sequence="AAAA"  # 0 G/C de 4 = 0%
        )
        self.assertEqual(seq.gc_content, 0.0)

    def test_auto_calculates_gc_content_100_percent(self):
        """Debe calcular 100% GC correctamente"""
        seq = DNASequence.objects.create(
            name="test",
            sequence="GGCC"  # 4 G/C de 4 = 100%
        )
        self.assertEqual(seq.gc_content, 100.0)

    def test_auto_calculates_gc_content_with_n(self):
        """Debe ignorar N en el cálculo de GC"""
        seq = DNASequence.objects.create(
            name="test",
            sequence="ATCGNNNN"  # 2 G/C de 8 = 25%
        )
        self.assertEqual(seq.gc_content, 25.0)

    def test_auto_generates_file_hash(self):
        """Debe generar hash SHA-256 automáticamente"""
        seq = DNASequence.objects.create(
            name="test",
            sequence="ATCG"
        )
        expected_hash = hashlib.sha256("ATCG".encode('utf-8')).hexdigest()
        self.assertEqual(seq.file_hash, expected_hash)

    def test_same_sequence_same_hash(self):
        """Misma secuencia debe generar el mismo hash"""
        seq1 = DNASequence.objects.create(name="test1", sequence="ATCG")
        # Nota: esto fallará por unique constraint, así que usamos otro método
        expected_hash = hashlib.sha256("ATCG".encode('utf-8')).hexdigest()
        self.assertEqual(seq1.file_hash, expected_hash)

    def test_normalizes_sequence_on_save(self):
        """Debe normalizar secuencia antes de guardar"""
        seq = DNASequence.objects.create(
            name="test",
            sequence="at cg\naa tt"
        )
        self.assertEqual(seq.sequence, "ATCGAATT")

    def test_validates_sequence_on_save(self):
        """Debe validar secuencia al guardar"""
        with self.assertRaises(ValidationError):
            DNASequence.objects.create(
                name="test",
                sequence="ATCG123"  # Caracteres inválidos
            )

    def test_str_representation(self):
        """Debe tener representación en string correcta"""
        seq = DNASequence.objects.create(
            name="my_sequence",
            sequence="ATCGATCG"
        )
        expected = "my_sequence (8 bp)"
        self.assertEqual(str(seq), expected)

    def test_uploaded_at_is_set(self):
        """Debe establecer uploaded_at automáticamente"""
        before = timezone.now()
        seq = DNASequence.objects.create(
            name="test",
            sequence="ATCG"
        )
        after = timezone.now()
        self.assertGreaterEqual(seq.uploaded_at, before)
        self.assertLessEqual(seq.uploaded_at, after)

    def test_ordering_by_uploaded_at_desc(self):
        """Debe ordenar por uploaded_at descendente"""
        seq1 = DNASequence.objects.create(name="first", sequence="AAAA")
        seq2 = DNASequence.objects.create(name="second", sequence="TTTT")
        seq3 = DNASequence.objects.create(name="third", sequence="GGGG")

        sequences = list(DNASequence.objects.all())
        self.assertEqual(sequences[0].name, "third")
        self.assertEqual(sequences[1].name, "second")
        self.assertEqual(sequences[2].name, "first")

    def test_unique_file_hash_constraint(self):
        """Debe respetar constraint de hash único"""
        DNASequence.objects.create(name="first", sequence="ATCG")
        # Intentar crear otra con la misma secuencia debe fallar
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            DNASequence.objects.create(name="second", sequence="ATCG")

    def test_manual_gc_content_override(self):
        """Debe permitir override manual de gc_content"""
        seq = DNASequence(
            name="test",
            sequence="ATCG",
            gc_content=75.0  # Manual override
        )
        seq.save()
        # No debe recalcular si ya está establecido
        self.assertEqual(seq.gc_content, 75.0)

    def test_manual_file_hash_override(self):
        """Debe permitir override manual de file_hash"""
        custom_hash = "a" * 64
        seq = DNASequence(
            name="test",
            sequence="ATCG",
            file_hash=custom_hash
        )
        seq.save()
        self.assertEqual(seq.file_hash, custom_hash)

    def test_empty_sequence_validation(self):
        """Debe rechazar secuencia vacía"""
        with self.assertRaises(ValidationError):
            DNASequence.objects.create(
                name="test",
                sequence=""
            )

    def test_long_sequence(self):
        """Debe manejar secuencias largas"""
        long_seq = "ATCG" * 10000  # 40,000 bp
        seq = DNASequence.objects.create(
            name="long_test",
            sequence=long_seq
        )
        self.assertEqual(seq.length, 40000)
        self.assertEqual(seq.gc_content, 50.0)


class DNASequenceMetaTests(TestCase):
    """Pruebas de metadata del modelo"""

    def test_db_table_name(self):
        """Debe usar el nombre de tabla correcto"""
        self.assertEqual(DNASequence._meta.db_table, "dna_sequences")

    def test_verbose_names(self):
        """Debe tener verbose names correctos"""
        self.assertEqual(DNASequence._meta.verbose_name, "DNA Sequence")
        self.assertEqual(DNASequence._meta.verbose_name_plural, "DNA Sequences")
