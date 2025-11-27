"""
Pruebas unitarias para search_api/models.py

Cubre:
- SearchJob model
- SearchResult model
- Estados de jobs
- Métodos mark_as_processing, mark_as_completed, mark_as_failed
- Relaciones entre modelos
"""

from django.test import TestCase
from django.utils import timezone

from sequences_api.models import DNASequence
from search_api.models import SearchJob, SearchResult


class SearchJobModelTests(TestCase):
    """Pruebas para el modelo SearchJob"""

    def setUp(self):
        self.sequence = DNASequence.objects.create(
            name="test_sequence",
            sequence="ATCGATCGATCG"
        )

    def test_create_search_job(self):
        """Debe crear un job de búsqueda básico"""
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG",
            allow_overlapping=True
        )
        self.assertIsNotNone(job.id)
        self.assertEqual(job.pattern, "ATG")
        self.assertEqual(job.status, 'PENDING')

    def test_default_status_is_pending(self):
        """Estado por defecto debe ser PENDING"""
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG"
        )
        self.assertEqual(job.status, 'PENDING')

    def test_default_allow_overlapping_is_true(self):
        """allow_overlapping debe ser True por defecto"""
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG"
        )
        self.assertTrue(job.allow_overlapping)

    def test_mark_as_processing(self):
        """Debe cambiar estado a PROCESSING"""
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG"
        )
        job.mark_as_processing()

        job.refresh_from_db()
        self.assertEqual(job.status, 'PROCESSING')

    def test_mark_as_completed(self):
        """Debe marcar como completado con métricas"""
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG"
        )

        before = timezone.now()
        job.mark_as_completed(
            total_matches=5,
            search_time_ms=123.45,
            algorithm_used="KMP"
        )
        after = timezone.now()

        job.refresh_from_db()
        self.assertEqual(job.status, 'COMPLETED')
        self.assertEqual(job.total_matches, 5)
        self.assertEqual(job.search_time_ms, 123.45)
        self.assertEqual(job.algorithm_used, "KMP")
        self.assertIsNotNone(job.completed_at)
        self.assertGreaterEqual(job.completed_at, before)
        self.assertLessEqual(job.completed_at, after)

    def test_mark_as_failed(self):
        """Debe marcar como fallido con mensaje de error"""
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG"
        )

        before = timezone.now()
        job.mark_as_failed("Connection timeout")
        after = timezone.now()

        job.refresh_from_db()
        self.assertEqual(job.status, 'FAILED')
        self.assertEqual(job.error_message, "Connection timeout")
        self.assertIsNotNone(job.completed_at)
        self.assertGreaterEqual(job.completed_at, before)
        self.assertLessEqual(job.completed_at, after)

    def test_str_representation(self):
        """Debe tener representación en string correcta"""
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG",
            status='PROCESSING'
        )
        expected = f"Search 'ATG' in test_sequence (PROCESSING)"
        self.assertEqual(str(job), expected)

    def test_created_at_is_set(self):
        """Debe establecer created_at automáticamente"""
        before = timezone.now()
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG"
        )
        after = timezone.now()

        self.assertGreaterEqual(job.created_at, before)
        self.assertLessEqual(job.created_at, after)

    def test_ordering_by_created_at_desc(self):
        """Debe ordenar por created_at descendente"""
        job1 = SearchJob.objects.create(sequence=self.sequence, pattern="ATG")
        job2 = SearchJob.objects.create(sequence=self.sequence, pattern="TAA")
        job3 = SearchJob.objects.create(sequence=self.sequence, pattern="GGG")

        jobs = list(SearchJob.objects.all())
        self.assertEqual(jobs[0].pattern, "GGG")
        self.assertEqual(jobs[1].pattern, "TAA")
        self.assertEqual(jobs[2].pattern, "ATG")

    def test_relationship_with_sequence(self):
        """Debe tener relación correcta con DNASequence"""
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG"
        )
        self.assertEqual(job.sequence.id, self.sequence.id)
        self.assertIn(job, self.sequence.search_jobs.all())

    def test_cascade_delete_from_sequence(self):
        """Debe eliminar jobs al eliminar secuencia (CASCADE)"""
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG"
        )
        job_id = job.id

        self.sequence.delete()

        self.assertFalse(SearchJob.objects.filter(id=job_id).exists())

    def test_long_pattern(self):
        """Debe manejar patrones largos (hasta 1000 caracteres)"""
        long_pattern = "ATCG" * 250  # 1000 caracteres
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern=long_pattern
        )
        self.assertEqual(len(job.pattern), 1000)

    def test_status_choices(self):
        """Debe validar status choices"""
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG"
        )

        # Verificar que los choices existen
        status_values = [choice[0] for choice in SearchJob.STATUS_CHOICES]
        self.assertIn('PENDING', status_values)
        self.assertIn('PROCESSING', status_values)
        self.assertIn('COMPLETED', status_values)
        self.assertIn('FAILED', status_values)


class SearchResultModelTests(TestCase):
    """Pruebas para el modelo SearchResult"""

    def setUp(self):
        self.sequence = DNASequence.objects.create(
            name="test_sequence",
            sequence="ATCGATCGATCG"
        )
        self.job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG"
        )

    def test_create_search_result(self):
        """Debe crear un resultado de búsqueda"""
        result = SearchResult.objects.create(
            job=self.job,
            position=5,
            context_before="ATCGA",
            context_after="ATCG"
        )
        self.assertIsNotNone(result.id)
        self.assertEqual(result.position, 5)

    def test_str_representation(self):
        """Debe tener representación en string correcta"""
        result = SearchResult.objects.create(
            job=self.job,
            position=42
        )
        expected = f"Match at position 42 in job #{self.job.id}"
        self.assertEqual(str(result), expected)

    def test_relationship_with_job(self):
        """Debe tener relación correcta con SearchJob"""
        result = SearchResult.objects.create(
            job=self.job,
            position=5
        )
        self.assertEqual(result.job.id, self.job.id)
        self.assertIn(result, self.job.results.all())

    def test_cascade_delete_from_job(self):
        """Debe eliminar resultados al eliminar job (CASCADE)"""
        result = SearchResult.objects.create(
            job=self.job,
            position=5
        )
        result_id = result.id

        self.job.delete()

        self.assertFalse(SearchResult.objects.filter(id=result_id).exists())

    def test_ordering_by_position_asc(self):
        """Debe ordenar por position ascendente"""
        result3 = SearchResult.objects.create(job=self.job, position=30)
        result1 = SearchResult.objects.create(job=self.job, position=10)
        result2 = SearchResult.objects.create(job=self.job, position=20)

        results = list(SearchResult.objects.all())
        self.assertEqual(results[0].position, 10)
        self.assertEqual(results[1].position, 20)
        self.assertEqual(results[2].position, 30)

    def test_context_fields_optional(self):
        """Campos de contexto deben ser opcionales"""
        result = SearchResult.objects.create(
            job=self.job,
            position=5
        )
        self.assertEqual(result.context_before, "")
        self.assertEqual(result.context_after, "")

    def test_context_fields_max_length(self):
        """Campos de contexto pueden tener hasta 50 caracteres"""
        long_context = "A" * 50
        result = SearchResult.objects.create(
            job=self.job,
            position=5,
            context_before=long_context,
            context_after=long_context
        )
        self.assertEqual(len(result.context_before), 50)
        self.assertEqual(len(result.context_after), 50)

    def test_large_position_value(self):
        """Debe manejar posiciones grandes (BigIntegerField)"""
        large_position = 1_000_000_000  # 1 billion
        result = SearchResult.objects.create(
            job=self.job,
            position=large_position
        )
        self.assertEqual(result.position, large_position)

    def test_multiple_results_for_same_job(self):
        """Debe permitir múltiples resultados para el mismo job"""
        result1 = SearchResult.objects.create(job=self.job, position=5)
        result2 = SearchResult.objects.create(job=self.job, position=10)
        result3 = SearchResult.objects.create(job=self.job, position=15)

        results = list(self.job.results.all())
        self.assertEqual(len(results), 3)


class SearchJobSearchResultIntegrationTests(TestCase):
    """Pruebas de integración entre SearchJob y SearchResult"""

    def setUp(self):
        self.sequence = DNASequence.objects.create(
            name="test_sequence",
            sequence="ATGATGATG"  # ATG aparece 3 veces
        )

    def test_complete_search_workflow(self):
        """Debe completar workflow completo de búsqueda"""
        # 1. Crear job
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG"
        )
        self.assertEqual(job.status, 'PENDING')

        # 2. Marcar como procesando
        job.mark_as_processing()
        self.assertEqual(job.status, 'PROCESSING')

        # 3. Crear resultados
        SearchResult.objects.create(job=job, position=0)
        SearchResult.objects.create(job=job, position=3)
        SearchResult.objects.create(job=job, position=6)

        # 4. Marcar como completado
        job.mark_as_completed(
            total_matches=3,
            search_time_ms=50.0,
            algorithm_used="naive-local"
        )

        # 5. Verificar
        self.assertEqual(job.status, 'COMPLETED')
        self.assertEqual(job.total_matches, 3)
        self.assertEqual(job.results.count(), 3)

    def test_failed_search_workflow(self):
        """Debe manejar workflow de búsqueda fallida"""
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG"
        )

        job.mark_as_processing()
        job.mark_as_failed("gRPC timeout")

        self.assertEqual(job.status, 'FAILED')
        self.assertEqual(job.error_message, "gRPC timeout")
        self.assertEqual(job.results.count(), 0)


class SearchJobMetaTests(TestCase):
    """Pruebas de metadata del modelo SearchJob"""

    def test_db_table_name(self):
        """Debe usar el nombre de tabla correcto"""
        self.assertEqual(SearchJob._meta.db_table, "search_jobs")

    def test_verbose_names(self):
        """Debe tener verbose names correctos"""
        self.assertEqual(SearchJob._meta.verbose_name, "Search Job")
        self.assertEqual(SearchJob._meta.verbose_name_plural, "Search Jobs")


class SearchResultMetaTests(TestCase):
    """Pruebas de metadata del modelo SearchResult"""

    def test_db_table_name(self):
        """Debe usar el nombre de tabla correcto"""
        self.assertEqual(SearchResult._meta.db_table, "search_results")

    def test_verbose_names(self):
        """Debe tener verbose names correctos"""
        self.assertEqual(SearchResult._meta.verbose_name, "Search Result")
        self.assertEqual(SearchResult._meta.verbose_name_plural, "Search Results")
