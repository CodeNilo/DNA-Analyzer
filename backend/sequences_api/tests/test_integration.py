"""
Pruebas de integración para sequences_api

Cubre:
- Integración entre serializers, models y database
- Upload completo + guardado en BD
- Detección de duplicados
- Validación en pipeline completo
"""

import io
from django.test import TestCase
from django.db import IntegrityError

from sequences_api.models import DNASequence
from sequences_api.serializers import DNASequenceUploadSerializer, DNASequenceSerializer


class SequenceUploadIntegrationTests(TestCase):
    """Pruebas de integración para carga de secuencias"""

    def create_mock_file(self, content, filename="test.txt"):
        """Helper para crear archivos mock"""
        file_obj = io.BytesIO(content.encode('utf-8'))
        file_obj.name = filename
        file_obj.size = len(content.encode('utf-8'))
        return file_obj

    def test_complete_upload_flow(self):
        """Pipeline completo: upload -> parse -> validate -> save -> BD"""
        content = "at cg\nat cg"
        file_obj = self.create_mock_file(content)

        # 1. Upload vía serializer
        serializer = DNASequenceUploadSerializer(data={
            'file': file_obj,
            'name': 'integration_test'
        })
        self.assertTrue(serializer.is_valid())
        instance = serializer.save()

        # 2. Verificar en BD
        db_instance = DNASequence.objects.get(id=instance.id)
        self.assertEqual(db_instance.name, 'integration_test')
        self.assertEqual(db_instance.sequence, 'ATCGATCG')
        self.assertEqual(db_instance.length, 8)
        self.assertEqual(db_instance.gc_content, 50.0)
        self.assertIsNotNone(db_instance.file_hash)

    def test_duplicate_detection_integration(self):
        """Debe detectar duplicados usando hash en BD"""
        content = "ATCGATCG"

        # Primera carga
        file1 = self.create_mock_file(content, "file1.txt")
        serializer1 = DNASequenceUploadSerializer(data={'file': file1})
        serializer1.is_valid()
        instance1 = serializer1.save()

        # Segunda carga (mismo contenido)
        file2 = self.create_mock_file(content, "file2.txt")
        serializer2 = DNASequenceUploadSerializer(data={'file': file2})
        serializer2.is_valid()
        instance2 = serializer2.save()

        # Debe devolver la misma instancia
        self.assertEqual(instance1.id, instance2.id)
        self.assertEqual(DNASequence.objects.count(), 1)

    def test_fasta_format_integration(self):
        """Pipeline completo con formato FASTA"""
        content = ">sequence_header\nATCG\nATCG"
        file_obj = self.create_mock_file(content, "seq.fasta")

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        serializer.is_valid()
        instance = serializer.save()

        db_instance = DNASequence.objects.get(id=instance.id)
        self.assertEqual(db_instance.sequence, 'ATCGATCG')

    def test_gc_content_calculated_on_save(self):
        """GC content debe calcularse automáticamente al guardar"""
        content = "GGCC"  # 100% GC
        file_obj = self.create_mock_file(content)

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        serializer.is_valid()
        instance = serializer.save()

        db_instance = DNASequence.objects.get(id=instance.id)
        self.assertEqual(db_instance.gc_content, 100.0)

    def test_normalization_in_full_pipeline(self):
        """Normalización debe aplicarse en todo el pipeline"""
        content = "at cg\naa tt"  # Minúsculas y saltos de línea
        file_obj = self.create_mock_file(content)

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        serializer.is_valid()
        instance = serializer.save()

        db_instance = DNASequence.objects.get(id=instance.id)
        self.assertEqual(db_instance.sequence, 'ATCGAATT')  # Normalizado

    def test_validation_failure_integration(self):
        """Validación debe fallar antes de llegar a BD"""
        content = "ATCG123XYZ"  # Inválido
        file_obj = self.create_mock_file(content)

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})

        with self.assertRaises(Exception):  # ValidationError o similar
            serializer.is_valid(raise_exception=True)
            serializer.save()

        # No debe haber creado registro en BD
        self.assertEqual(DNASequence.objects.count(), 0)

    def test_multiple_sequences_ordering(self):
        """Múltiples secuencias deben ordenarse por uploaded_at desc"""
        seq1 = self.create_mock_file("AAAA", "seq1.txt")
        seq2 = self.create_mock_file("TTTT", "seq2.txt")
        seq3 = self.create_mock_file("GGGG", "seq3.txt")

        for file_obj in [seq1, seq2, seq3]:
            serializer = DNASequenceUploadSerializer(data={'file': file_obj})
            serializer.is_valid()
            serializer.save()

        sequences = list(DNASequence.objects.all())
        # El más reciente primero
        self.assertEqual(sequences[0].sequence, 'GGGG')
        self.assertEqual(sequences[1].sequence, 'TTTT')
        self.assertEqual(sequences[2].sequence, 'AAAA')

    def test_hash_uniqueness_constraint(self):
        """Constraint de BD debe prevenir duplicados con mismo hash"""
        # Crear primera secuencia directamente en BD
        DNASequence.objects.create(name="first", sequence="ATCG")

        # Intentar crear otra con la misma secuencia directamente
        with self.assertRaises(IntegrityError):
            DNASequence.objects.create(name="second", sequence="ATCG")

    def test_serializer_read_integration(self):
        """Serializer de lectura debe funcionar con instancias de BD"""
        # Crear en BD
        instance = DNASequence.objects.create(
            name="test_read",
            sequence="ATCGATCG"
        )

        # Serializar para lectura
        serializer = DNASequenceSerializer(instance)
        data = serializer.data

        self.assertEqual(data['name'], 'test_read')
        self.assertEqual(data['length'], 8)
        self.assertEqual(data['gc_content'], 50.0)
        self.assertIn('id', data)
        self.assertNotIn('sequence', data)  # No debe exponerse

    def test_large_file_integration(self):
        """Debe manejar archivos grandes correctamente"""
        large_content = "ATCG" * 10000  # 40k bp
        file_obj = self.create_mock_file(large_content)

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        self.assertTrue(serializer.is_valid())
        instance = serializer.save()

        db_instance = DNASequence.objects.get(id=instance.id)
        self.assertEqual(db_instance.length, 40000)
        self.assertIsNotNone(db_instance.file_hash)

    def test_csv_with_commas_integration(self):
        """Debe parsear CSV y eliminar comas correctamente"""
        content = "A,T,C,G,A,T,C,G"
        file_obj = self.create_mock_file(content, "seq.csv")

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        serializer.is_valid()
        instance = serializer.save()

        db_instance = DNASequence.objects.get(id=instance.id)
        self.assertEqual(db_instance.sequence, 'ATCGATCG')

    def test_sequence_with_n_integration(self):
        """Debe manejar secuencias con N correctamente"""
        content = "ATCGNATCG"
        file_obj = self.create_mock_file(content)

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})
        serializer.is_valid()
        instance = serializer.save()

        db_instance = DNASequence.objects.get(id=instance.id)
        self.assertEqual(db_instance.sequence, 'ATCGNATCG')
        # GC content debe ignorar N
        self.assertEqual(db_instance.gc_content, 25.0)  # 2 GC de 8 total

    def test_empty_file_integration(self):
        """Debe rechazar archivo vacío en el pipeline"""
        content = ""
        file_obj = self.create_mock_file(content)

        serializer = DNASequenceUploadSerializer(data={'file': file_obj})

        with self.assertRaises(Exception):
            serializer.is_valid(raise_exception=True)
            serializer.save()

        self.assertEqual(DNASequence.objects.count(), 0)


class SequenceQueryIntegrationTests(TestCase):
    """Pruebas de integración para queries de secuencias"""

    def test_filter_by_date_range(self):
        """Debe filtrar secuencias por rango de fechas"""
        from django.utils import timezone
        from datetime import timedelta

        # Crear secuencias con diferentes fechas
        old_seq = DNASequence.objects.create(name="old", sequence="AAAA")
        old_seq.uploaded_at = timezone.now() - timedelta(days=10)
        old_seq.save()

        recent_seq = DNASequence.objects.create(name="recent", sequence="TTTT")

        # Filtrar últimas 7 días
        cutoff = timezone.now() - timedelta(days=7)
        recent_sequences = DNASequence.objects.filter(uploaded_at__gte=cutoff)

        self.assertIn(recent_seq, recent_sequences)
        self.assertNotIn(old_seq, recent_sequences)

    def test_search_by_gc_content_range(self):
        """Debe buscar secuencias por rango de GC content"""
        DNASequence.objects.create(name="low_gc", sequence="AAAA")  # 0%
        DNASequence.objects.create(name="mid_gc", sequence="ATCG")  # 50%
        DNASequence.objects.create(name="high_gc", sequence="GGCC")  # 100%

        mid_range = DNASequence.objects.filter(
            gc_content__gte=25.0,
            gc_content__lte=75.0
        )

        self.assertEqual(mid_range.count(), 1)
        self.assertEqual(mid_range.first().name, "mid_gc")

    def test_search_by_length_range(self):
        """Debe buscar secuencias por rango de longitud"""
        DNASequence.objects.create(name="short", sequence="AT")  # 2 bp
        DNASequence.objects.create(name="medium", sequence="ATCGATCG")  # 8 bp
        DNASequence.objects.create(name="long", sequence="ATCG" * 100)  # 400 bp

        medium_length = DNASequence.objects.filter(
            length__gte=5,
            length__lte=20
        )

        self.assertEqual(medium_length.count(), 1)
        self.assertEqual(medium_length.first().name, "medium")
