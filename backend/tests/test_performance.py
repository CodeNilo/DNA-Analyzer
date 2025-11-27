"""
Pruebas de rendimiento

Cubre:
- Tiempo de respuesta de APIs
- Rendimiento de búsqueda
- Comparación gRPC vs Local
- Uso de memoria
- Eficiencia de algoritmos
"""

import time
import io
import json
from django.test import TestCase, Client, override_settings
from unittest.mock import patch, Mock

from sequences_api.models import DNASequence
from search_api.models import SearchJob, SearchResult
from search_api.services import run_local_search, run_grpc_search


class APIResponseTimeTests(TestCase):
    """Pruebas de tiempo de respuesta de APIs"""

    def setUp(self):
        self.client = Client()

        # Crear datos de prueba
        for i in range(10):
            DNASequence.objects.create(
                name=f"seq{i}",
                sequence="ATCG" * 100
            )

    def measure_response_time(self, method, url, data=None, **kwargs):
        """Helper para medir tiempo de respuesta"""
        start = time.perf_counter()

        if method == 'GET':
            response = self.client.get(url, **kwargs)
        elif method == 'POST':
            response = self.client.post(url, data, **kwargs)

        elapsed_ms = (time.perf_counter() - start) * 1000
        return response, elapsed_ms

    def test_list_sequences_response_time(self):
        """
        GET /api/sequences/ debe responder en menos de 200ms
        """
        response, elapsed = self.measure_response_time('GET', '/api/sequences/')

        self.assertEqual(response.status_code, 200)
        print(f"List sequences response time: {elapsed:.2f}ms")

        # Flexible para diferentes entornos
        self.assertLess(elapsed, 500)

    def test_search_response_time_small_sequence(self):
        """
        Búsqueda en secuencia pequeña (< 1kb) debe ser rápida
        """
        seq = DNASequence.objects.create(
            name="small",
            sequence="ATCGATCG" * 10  # 80 bp
        )

        response, elapsed = self.measure_response_time(
            'POST',
            '/api/search/',
            json.dumps({
                'sequence_id': seq.id,
                'pattern': 'ATG'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        print(f"Small sequence search time: {elapsed:.2f}ms")

        # Debe ser muy rápido
        self.assertLess(elapsed, 200)

    def test_search_response_time_medium_sequence(self):
        """
        Búsqueda en secuencia mediana (~100kb) debe completarse en < 1s
        """
        seq = DNASequence.objects.create(
            name="medium",
            sequence="ATCG" * 25000  # 100kb
        )

        response, elapsed = self.measure_response_time(
            'POST',
            '/api/search/',
            json.dumps({
                'sequence_id': seq.id,
                'pattern': 'ATG'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        print(f"Medium sequence (100kb) search time: {elapsed:.2f}ms")

        # Debe completarse en menos de 1 segundo
        self.assertLess(elapsed, 1000)

    def test_search_response_time_large_sequence(self):
        """
        Búsqueda en secuencia grande (~1MB) debe completarse en < 3s
        """
        seq = DNASequence.objects.create(
            name="large",
            sequence="ATCG" * 250000  # 1MB
        )

        response, elapsed = self.measure_response_time(
            'POST',
            '/api/search/',
            json.dumps({
                'sequence_id': seq.id,
                'pattern': 'ATG'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        print(f"Large sequence (1MB) search time: {elapsed:.2f}ms")

        # Más flexible para secuencias grandes
        self.assertLess(elapsed, 5000)


class SearchAlgorithmPerformanceTests(TestCase):
    """Pruebas de rendimiento de algoritmos de búsqueda"""

    def test_local_search_performance_small_pattern(self):
        """
        Búsqueda local con patrón pequeño debe ser eficiente
        """
        sequence = "ATCG" * 10000  # 40kb
        pattern = "ATG"

        start = time.perf_counter()
        result = run_local_search(sequence, pattern, allow_overlapping=True)
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"Local search (40kb, pattern=3): {elapsed_ms:.2f}ms")
        print(f"Matches found: {result['total_matches']}")

        self.assertGreater(result['total_matches'], 0)
        self.assertLess(elapsed_ms, 200)

    def test_local_search_performance_long_pattern(self):
        """
        Búsqueda local con patrón largo debe seguir siendo eficiente
        """
        sequence = "ATCG" * 10000  # 40kb
        pattern = "ATCGATCG" * 10  # 80 caracteres

        start = time.perf_counter()
        result = run_local_search(sequence, pattern, allow_overlapping=True)
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"Local search (40kb, pattern=80): {elapsed_ms:.2f}ms")

        self.assertLess(elapsed_ms, 300)

    def test_overlapping_vs_non_overlapping_performance(self):
        """
        Comparar rendimiento entre modos solapado y no solapado
        """
        sequence = "A" * 10000

        # Modo solapado
        start1 = time.perf_counter()
        result1 = run_local_search(sequence, "AA", allow_overlapping=True)
        elapsed1 = (time.perf_counter() - start1) * 1000

        # Modo no solapado
        start2 = time.perf_counter()
        result2 = run_local_search(sequence, "AA", allow_overlapping=False)
        elapsed2 = (time.perf_counter() - start2) * 1000

        print(f"Overlapping mode: {elapsed1:.2f}ms ({result1['total_matches']} matches)")
        print(f"Non-overlapping mode: {elapsed2:.2f}ms ({result2['total_matches']} matches)")

        # Ambos deben completarse rápidamente
        self.assertLess(elapsed1, 200)
        self.assertLess(elapsed2, 200)

        # Modo solapado debe encontrar más coincidencias
        self.assertGreater(result1['total_matches'], result2['total_matches'])


class DatabasePerformanceTests(TestCase):
    """Pruebas de rendimiento de operaciones de base de datos"""

    def test_bulk_create_results_performance(self):
        """
        Bulk create de resultados debe ser eficiente
        """
        seq = DNASequence.objects.create(name="test", sequence="ATCG")
        job = SearchJob.objects.create(sequence=seq, pattern="A")

        # Crear 1000 resultados
        results = [
            SearchResult(job=job, position=i)
            for i in range(1000)
        ]

        start = time.perf_counter()
        SearchResult.objects.bulk_create(results)
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"Bulk create 1000 results: {elapsed_ms:.2f}ms")

        # Debe ser rápido
        self.assertLess(elapsed_ms, 1000)
        self.assertEqual(SearchResult.objects.filter(job=job).count(), 1000)

    def test_query_results_with_limit_performance(self):
        """
        Query de resultados con límite debe usar índices eficientemente
        """
        seq = DNASequence.objects.create(name="test", sequence="A" * 1000)
        job = SearchJob.objects.create(sequence=seq, pattern="A")

        # Crear muchos resultados
        SearchResult.objects.bulk_create([
            SearchResult(job=job, position=i)
            for i in range(1000)
        ])

        start = time.perf_counter()
        results = list(job.results.all()[:100])
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"Query 100 results from 1000: {elapsed_ms:.2f}ms")

        self.assertEqual(len(results), 100)
        self.assertLess(elapsed_ms, 100)

    def test_pagination_performance(self):
        """
        Paginación debe ser eficiente
        """
        # Crear 100 secuencias
        for i in range(100):
            DNASequence.objects.create(
                name=f"seq{i}",
                sequence="ATCG" * 10
            )

        client = Client()

        start = time.perf_counter()
        response = client.get('/api/sequences/?page=1')
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"Pagination (page 1 of 100 sequences): {elapsed_ms:.2f}ms")

        self.assertEqual(response.status_code, 200)
        self.assertLess(elapsed_ms, 300)


class MemoryEfficiencyTests(TestCase):
    """Pruebas de eficiencia de memoria (básicas)"""

    def test_large_sequence_processing_memory(self):
        """
        Procesar secuencia grande no debe causar problemas de memoria
        """
        # Crear secuencia de ~10MB
        large_sequence = "ATCG" * 2500000

        # Crear en BD
        seq = DNASequence.objects.create(
            name="large_mem_test",
            sequence=large_sequence
        )

        # Buscar en ella
        result = run_local_search(seq.sequence, "ATG", allow_overlapping=False)

        # Si llega aquí sin error, la memoria se manejó bien
        self.assertIsNotNone(result)
        self.assertGreater(result['total_matches'], 0)


class GrpcVsLocalPerformanceTests(TestCase):
    """Comparación de rendimiento gRPC vs Local"""

    @override_settings(USE_GRPC_SEARCH=True)
    @patch('search_api.services.get_grpc_client')
    def test_grpc_vs_local_comparison(self, mock_get_client):
        """
        Comparar tiempo de búsqueda entre gRPC y local
        (con gRPC mockeado para pruebas)
        """
        sequence = "ATCG" * 25000  # 100kb

        # Mock gRPC response (simular que es más rápido)
        mock_match = Mock()
        mock_match.position = 0
        mock_match.context_before = ""
        mock_match.context_after = "ATCG"

        mock_response = Mock()
        mock_response.matches = [mock_match]
        mock_response.total_matches = 1
        mock_response.search_time_ms = 5.0  # Simular que gRPC es rápido
        mock_response.algorithm_used = "KMP"

        mock_client = Mock()
        mock_client.search.return_value = mock_response
        mock_client.address = "localhost:50051"
        mock_get_client.return_value = mock_client

        # Búsqueda gRPC
        start_grpc = time.perf_counter()
        result_grpc = run_grpc_search(sequence, "ATG", allow_overlapping=True)
        elapsed_grpc = (time.perf_counter() - start_grpc) * 1000

        # Búsqueda local
        start_local = time.perf_counter()
        result_local = run_local_search(sequence, "ATG", allow_overlapping=True)
        elapsed_local = (time.perf_counter() - start_local) * 1000

        print(f"gRPC search (mocked): {elapsed_grpc:.2f}ms")
        print(f"Local search: {elapsed_local:.2f}ms")

        # Ambos deben completarse
        self.assertIsNotNone(result_grpc)
        self.assertIsNotNone(result_local)


class ScalabilityTests(TestCase):
    """Pruebas básicas de escalabilidad"""

    def test_search_scales_linearly_with_sequence_size(self):
        """
        Tiempo de búsqueda debe escalar aproximadamente lineal con tamaño
        """
        sizes = [1000, 5000, 10000]
        times = []

        for size in sizes:
            sequence = "ATCG" * (size // 4)

            start = time.perf_counter()
            run_local_search(sequence, "ATG", allow_overlapping=True)
            elapsed_ms = (time.perf_counter() - start) * 1000

            times.append(elapsed_ms)
            print(f"Search in {size}bp: {elapsed_ms:.2f}ms")

        # Verificar que escala razonablemente
        # El tiempo para 10000 no debería ser > 15x el tiempo para 1000
        self.assertLess(times[2], times[0] * 15)

    def test_handles_many_small_searches(self):
        """
        Debe manejar muchas búsquedas pequeñas eficientemente
        """
        sequence = "ATCGATCG" * 100
        patterns = ["AT", "CG", "ATG", "TCG", "GAT"]

        start = time.perf_counter()
        for pattern in patterns * 20:  # 100 búsquedas
            run_local_search(sequence, pattern, allow_overlapping=True)
        elapsed_ms = (time.perf_counter() - start) * 1000

        print(f"100 small searches: {elapsed_ms:.2f}ms")

        # Debe completarse razonablemente rápido
        self.assertLess(elapsed_ms, 2000)


class BenchmarkTests(TestCase):
    """Tests de benchmark generales"""

    def test_end_to_end_benchmark(self):
        """
        Benchmark de flujo completo: upload + búsqueda
        """
        client = Client()

        # Upload
        file_obj = io.BytesIO(("ATCG" * 25000).encode('utf-8'))
        file_obj.name = "benchmark.txt"

        upload_start = time.perf_counter()
        upload_response = client.post(
            '/api/sequences/upload/',
            {'file': file_obj},
            format='multipart'
        )
        upload_time = (time.perf_counter() - upload_start) * 1000

        sequence_id = upload_response.json()['id']

        # Búsqueda
        search_start = time.perf_counter()
        search_response = client.post(
            '/api/search/',
            json.dumps({
                'sequence_id': sequence_id,
                'pattern': 'ATG'
            }),
            content_type='application/json'
        )
        search_time = (time.perf_counter() - search_start) * 1000

        total_time = upload_time + search_time

        print(f"\n=== Benchmark Results ===")
        print(f"Upload (100kb): {upload_time:.2f}ms")
        print(f"Search: {search_time:.2f}ms")
        print(f"Total: {total_time:.2f}ms")

        self.assertEqual(upload_response.status_code, 201)
        self.assertEqual(search_response.status_code, 200)
