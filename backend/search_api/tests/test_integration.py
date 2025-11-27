"""
Pruebas de integración para search_api

Cubre:
- Integración completa de búsqueda
- Interacción entre services, models y BD
- Pipeline completo: create job -> search -> save results
- Integración con gRPC (mocked)
"""

from unittest.mock import Mock, patch
from django.test import TestCase, override_settings
import grpc

from sequences_api.models import DNASequence
from search_api.models import SearchJob, SearchResult
from search_api.services import run_search, run_local_search, run_grpc_search


class SearchIntegrationTests(TestCase):
    """Pruebas de integración para búsqueda completa"""

    def setUp(self):
        self.sequence = DNASequence.objects.create(
            name="test_sequence",
            sequence="ATGATGATGATG"  # ATG aparece 4 veces
        )

    def test_complete_search_flow_local(self):
        """Pipeline completo: crear job -> buscar local -> guardar resultados"""
        # 1. Crear job
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG",
            status='PENDING'
        )

        # 2. Marcar como procesando
        job.mark_as_processing()
        self.assertEqual(job.status, 'PROCESSING')

        # 3. Ejecutar búsqueda
        result_data = run_local_search(
            self.sequence.sequence,
            "ATG",
            allow_overlapping=True
        )

        # 4. Guardar resultados
        for match in result_data['matches']:
            SearchResult.objects.create(
                job=job,
                position=match['position'],
                context_before=match['context_before'],
                context_after=match['context_after']
            )

        # 5. Marcar como completado
        job.mark_as_completed(
            total_matches=result_data['total_matches'],
            search_time_ms=result_data['search_time_ms'],
            algorithm_used=result_data['algorithm_used']
        )

        # 6. Verificar en BD
        job.refresh_from_db()
        self.assertEqual(job.status, 'COMPLETED')
        self.assertEqual(job.total_matches, 4)
        self.assertEqual(job.algorithm_used, 'naive-local')
        self.assertEqual(job.results.count(), 4)

        # Verificar resultados individuales
        results = list(job.results.all().order_by('position'))
        self.assertEqual(results[0].position, 0)
        self.assertEqual(results[1].position, 3)
        self.assertEqual(results[2].position, 6)
        self.assertEqual(results[3].position, 9)

    def test_search_with_overlapping_integration(self):
        """Búsqueda con solapamiento debe guardar todos los matches"""
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="AA",
            allow_overlapping=True
        )

        # Crear secuencia con AAs consecutivas
        seq_with_aa = DNASequence.objects.create(
            name="aa_seq",
            sequence="AAAA"
        )
        job.sequence = seq_with_aa
        job.save()

        job.mark_as_processing()
        result_data = run_local_search(seq_with_aa.sequence, "AA", allow_overlapping=True)

        for match in result_data['matches']:
            SearchResult.objects.create(
                job=job,
                position=match['position'],
                context_before=match['context_before'],
                context_after=match['context_after']
            )

        job.mark_as_completed(
            total_matches=result_data['total_matches'],
            search_time_ms=result_data['search_time_ms'],
            algorithm_used=result_data['algorithm_used']
        )

        # Debe encontrar 3 coincidencias solapadas (pos 0, 1, 2)
        self.assertEqual(job.results.count(), 3)

    def test_search_without_overlapping_integration(self):
        """Búsqueda sin solapamiento debe guardar solo matches directos"""
        seq_with_aa = DNASequence.objects.create(
            name="aa_seq",
            sequence="AAAA"
        )

        job = SearchJob.objects.create(
            sequence=seq_with_aa,
            pattern="AA",
            allow_overlapping=False
        )

        job.mark_as_processing()
        result_data = run_local_search(seq_with_aa.sequence, "AA", allow_overlapping=False)

        for match in result_data['matches']:
            SearchResult.objects.create(
                job=job,
                position=match['position'],
                context_before=match['context_before'],
                context_after=match['context_after']
            )

        job.mark_as_completed(
            total_matches=result_data['total_matches'],
            search_time_ms=result_data['search_time_ms'],
            algorithm_used=result_data['algorithm_used']
        )

        # Debe encontrar 2 coincidencias no solapadas (pos 0, 2)
        self.assertEqual(job.results.count(), 2)

    def test_context_saved_correctly(self):
        """Contexto antes/después debe guardarse correctamente"""
        seq = DNASequence.objects.create(
            name="context_seq",
            sequence="AAAAAAAAAATCGAAAAAAAAAA"  # TCG en medio con contexto
        )

        job = SearchJob.objects.create(
            sequence=seq,
            pattern="TCG"
        )

        job.mark_as_processing()
        result_data = run_local_search(seq.sequence, "TCG", allow_overlapping=True)

        SearchResult.objects.create(
            job=job,
            position=result_data['matches'][0]['position'],
            context_before=result_data['matches'][0]['context_before'],
            context_after=result_data['matches'][0]['context_after']
        )

        job.mark_as_completed(
            total_matches=1,
            search_time_ms=result_data['search_time_ms'],
            algorithm_used=result_data['algorithm_used']
        )

        result = job.results.first()
        self.assertEqual(result.context_before, "AAAAAAAAAA")  # 10 As antes
        self.assertEqual(result.context_after, "AAAAAAAAAA")  # 10 As después

    def test_no_matches_integration(self):
        """Búsqueda sin coincidencias debe completarse correctamente"""
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="GGGGGGGG"  # Patrón que no existe
        )

        job.mark_as_processing()
        result_data = run_local_search(
            self.sequence.sequence,
            "GGGGGGGG",
            allow_overlapping=True
        )

        job.mark_as_completed(
            total_matches=result_data['total_matches'],
            search_time_ms=result_data['search_time_ms'],
            algorithm_used=result_data['algorithm_used']
        )

        job.refresh_from_db()
        self.assertEqual(job.status, 'COMPLETED')
        self.assertEqual(job.total_matches, 0)
        self.assertEqual(job.results.count(), 0)

    def test_failed_search_integration(self):
        """Búsqueda fallida debe marcarse correctamente"""
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG"
        )

        job.mark_as_processing()

        # Simular fallo
        try:
            raise ValueError("Simulated error")
        except Exception as e:
            job.mark_as_failed(str(e))

        job.refresh_from_db()
        self.assertEqual(job.status, 'FAILED')
        self.assertEqual(job.error_message, "Simulated error")
        self.assertIsNotNone(job.completed_at)
        self.assertEqual(job.results.count(), 0)

    def test_cascade_delete_integration(self):
        """Eliminar sequence debe eliminar jobs y results en cascada"""
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG"
        )

        SearchResult.objects.create(job=job, position=0)
        SearchResult.objects.create(job=job, position=3)

        job_id = job.id
        result_ids = list(job.results.values_list('id', flat=True))

        # Eliminar secuencia
        self.sequence.delete()

        # Verificar que se eliminaron job y results
        self.assertFalse(SearchJob.objects.filter(id=job_id).exists())
        self.assertFalse(SearchResult.objects.filter(id__in=result_ids).exists())

    def test_multiple_jobs_same_sequence(self):
        """Múltiples jobs pueden usar la misma secuencia"""
        job1 = SearchJob.objects.create(sequence=self.sequence, pattern="ATG")
        job2 = SearchJob.objects.create(sequence=self.sequence, pattern="TGA")
        job3 = SearchJob.objects.create(sequence=self.sequence, pattern="GAT")

        jobs = self.sequence.search_jobs.all()
        self.assertEqual(jobs.count(), 3)
        self.assertIn(job1, jobs)
        self.assertIn(job2, jobs)
        self.assertIn(job3, jobs)

    def test_large_result_set_integration(self):
        """Debe manejar conjuntos grandes de resultados"""
        # Crear secuencia con muchas repeticiones
        large_seq = DNASequence.objects.create(
            name="large",
            sequence="A" * 1000  # 1000 As
        )

        job = SearchJob.objects.create(
            sequence=large_seq,
            pattern="A"
        )

        job.mark_as_processing()
        result_data = run_local_search(large_seq.sequence, "A", allow_overlapping=True)

        # Bulk create results
        SearchResult.objects.bulk_create([
            SearchResult(
                job=job,
                position=match['position'],
                context_before=match['context_before'],
                context_after=match['context_after']
            )
            for match in result_data['matches']
        ])

        job.mark_as_completed(
            total_matches=result_data['total_matches'],
            search_time_ms=result_data['search_time_ms'],
            algorithm_used=result_data['algorithm_used']
        )

        # Debe haber 1000 resultados
        self.assertEqual(job.results.count(), 1000)
        self.assertEqual(job.total_matches, 1000)


class GrpcSearchIntegrationTests(TestCase):
    """Pruebas de integración con gRPC (mocked)"""

    def setUp(self):
        self.sequence = DNASequence.objects.create(
            name="grpc_test",
            sequence="ATGATGATG"
        )

    @override_settings(USE_GRPC_SEARCH=True)
    @patch('search_api.services.get_grpc_client')
    def test_grpc_search_integration(self, mock_get_client):
        """Búsqueda vía gRPC debe funcionar end-to-end"""
        # Mock gRPC response
        mock_match = Mock()
        mock_match.position = 0
        mock_match.context_before = ""
        mock_match.context_after = "ATGATG"

        mock_response = Mock()
        mock_response.matches = [mock_match]
        mock_response.total_matches = 1
        mock_response.search_time_ms = 15.5
        mock_response.algorithm_used = "KMP"

        mock_client = Mock()
        mock_client.search.return_value = mock_response
        mock_client.address = "localhost:50051"
        mock_get_client.return_value = mock_client

        # Crear job y ejecutar búsqueda
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG"
        )

        job.mark_as_processing()
        result_data = run_search(self.sequence.sequence, "ATG", allow_overlapping=True)

        SearchResult.objects.create(
            job=job,
            position=result_data['matches'][0]['position'],
            context_before=result_data['matches'][0]['context_before'],
            context_after=result_data['matches'][0]['context_after']
        )

        job.mark_as_completed(
            total_matches=result_data['total_matches'],
            search_time_ms=result_data['search_time_ms'],
            algorithm_used=result_data['algorithm_used']
        )

        # Verificar
        job.refresh_from_db()
        self.assertEqual(job.status, 'COMPLETED')
        self.assertEqual(job.algorithm_used, 'KMP')
        self.assertEqual(job.total_matches, 1)

    @override_settings(USE_GRPC_SEARCH=True)
    @patch('search_api.services.get_grpc_client')
    def test_grpc_fallback_integration(self, mock_get_client):
        """Debe hacer fallback a local si gRPC falla"""
        mock_client = Mock()
        mock_client.search.side_effect = grpc.RpcError()
        mock_client.address = "localhost:50051"
        mock_get_client.return_value = mock_client

        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG"
        )

        job.mark_as_processing()

        # Debe hacer fallback a local
        result_data = run_search(self.sequence.sequence, "ATG", allow_overlapping=True)

        for match in result_data['matches']:
            SearchResult.objects.create(
                job=job,
                position=match['position'],
                context_before=match['context_before'],
                context_after=match['context_after']
            )

        job.mark_as_completed(
            total_matches=result_data['total_matches'],
            search_time_ms=result_data['search_time_ms'],
            algorithm_used=result_data['algorithm_used']
        )

        # Debe haber usado algoritmo local
        job.refresh_from_db()
        self.assertEqual(job.algorithm_used, 'naive-local')
        self.assertEqual(job.status, 'COMPLETED')
        self.assertGreater(job.results.count(), 0)

    @override_settings(USE_GRPC_SEARCH=False)
    def test_local_only_integration(self):
        """Con gRPC deshabilitado, debe usar solo local"""
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG"
        )

        job.mark_as_processing()
        result_data = run_search(self.sequence.sequence, "ATG", allow_overlapping=True)

        for match in result_data['matches']:
            SearchResult.objects.create(
                job=job,
                position=match['position'],
                context_before=match['context_before'],
                context_after=match['context_after']
            )

        job.mark_as_completed(
            total_matches=result_data['total_matches'],
            search_time_ms=result_data['search_time_ms'],
            algorithm_used=result_data['algorithm_used']
        )

        job.refresh_from_db()
        self.assertEqual(job.algorithm_used, 'naive-local')
        self.assertEqual(job.status, 'COMPLETED')


class SearchPerformanceIntegrationTests(TestCase):
    """Pruebas de integración relacionadas con rendimiento"""

    def test_large_sequence_search_integration(self):
        """Debe manejar búsquedas en secuencias grandes"""
        large_seq = DNASequence.objects.create(
            name="large_seq",
            sequence="ATCG" * 10000  # 40k bp
        )

        job = SearchJob.objects.create(
            sequence=large_seq,
            pattern="ATG"
        )

        job.mark_as_processing()
        result_data = run_local_search(
            large_seq.sequence,
            "ATG",
            allow_overlapping=True
        )

        # Bulk create (más eficiente para grandes cantidades)
        SearchResult.objects.bulk_create([
            SearchResult(
                job=job,
                position=match['position'],
                context_before=match['context_before'],
                context_after=match['context_after']
            )
            for match in result_data['matches']
        ])

        job.mark_as_completed(
            total_matches=result_data['total_matches'],
            search_time_ms=result_data['search_time_ms'],
            algorithm_used=result_data['algorithm_used']
        )

        job.refresh_from_db()
        self.assertEqual(job.status, 'COMPLETED')
        self.assertGreater(job.total_matches, 0)
        self.assertIsInstance(job.search_time_ms, float)
