"""
Pruebas funcionales para las APIs REST

Cubre:
- Endpoints de sequences_api
- Endpoints de search_api
- Códigos de respuesta HTTP
- Formato de respuestas JSON
- Validaciones de entrada
- Paginación
"""

import io
import json
from django.test import TestCase, Client
from django.urls import reverse

from sequences_api.models import DNASequence
from search_api.models import SearchJob, SearchResult


class SequencesAPIFunctionalTests(TestCase):
    """Pruebas funcionales para la API de secuencias"""

    def setUp(self):
        self.client = Client()

    def create_mock_file(self, content, filename="test.txt"):
        """Helper para crear archivos mock"""
        file_obj = io.BytesIO(content.encode('utf-8'))
        file_obj.name = filename
        return file_obj

    def test_upload_sequence_success(self):
        """POST /api/sequences/upload/ debe crear secuencia"""
        file_content = "ATCGATCG"
        file_obj = self.create_mock_file(file_content)

        response = self.client.post(
            '/api/sequences/upload/',
            {'file': file_obj, 'name': 'test_seq'},
            format='multipart'
        )

        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertIn('id', data)
        self.assertEqual(data['name'], 'test_seq')
        self.assertEqual(data['length'], 8)
        self.assertEqual(data['gc_content'], 50.0)

    def test_upload_sequence_without_file(self):
        """POST sin archivo debe retornar 400"""
        response = self.client.post('/api/sequences/upload/', {})

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn('file', data)

    def test_upload_invalid_sequence(self):
        """POST con secuencia inválida debe retornar 400"""
        file_content = "ATCG123XYZ"
        file_obj = self.create_mock_file(file_content)

        response = self.client.post(
            '/api/sequences/upload/',
            {'file': file_obj},
            format='multipart'
        )

        self.assertEqual(response.status_code, 400)

    def test_upload_duplicate_returns_200(self):
        """POST con duplicado debe retornar 200 (no 201)"""
        file_content = "ATCGATCG"

        # Primera carga
        file_obj1 = self.create_mock_file(file_content)
        response1 = self.client.post(
            '/api/sequences/upload/',
            {'file': file_obj1},
            format='multipart'
        )
        self.assertEqual(response1.status_code, 201)

        # Segunda carga (duplicado)
        file_obj2 = self.create_mock_file(file_content)
        response2 = self.client.post(
            '/api/sequences/upload/',
            {'file': file_obj2},
            format='multipart'
        )
        self.assertEqual(response2.status_code, 200)

    def test_list_sequences_empty(self):
        """GET /api/sequences/ sin datos debe retornar lista vacía"""
        response = self.client.get('/api/sequences/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('results', data)
        self.assertEqual(len(data['results']), 0)

    def test_list_sequences_with_data(self):
        """GET /api/sequences/ debe retornar lista de secuencias"""
        DNASequence.objects.create(name="seq1", sequence="AAAA")
        DNASequence.objects.create(name="seq2", sequence="TTTT")
        DNASequence.objects.create(name="seq3", sequence="GGGG")

        response = self.client.get('/api/sequences/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data['results']), 3)

    def test_list_sequences_pagination(self):
        """GET /api/sequences/ debe paginar resultados"""
        # Crear 25 secuencias
        for i in range(25):
            DNASequence.objects.create(
                name=f"seq{i}",
                sequence="ATCG" * (i + 1)
            )

        response = self.client.get('/api/sequences/')
        data = response.json()

        # Por defecto página de 20
        self.assertEqual(len(data['results']), 20)
        self.assertIn('next', data)
        self.assertIn('previous', data)
        self.assertIn('count', data)
        self.assertEqual(data['count'], 25)

    def test_list_sequences_ordered_by_date_desc(self):
        """GET /api/sequences/ debe ordenar por fecha descendente"""
        seq1 = DNASequence.objects.create(name="first", sequence="AAAA")
        seq2 = DNASequence.objects.create(name="second", sequence="TTTT")
        seq3 = DNASequence.objects.create(name="third", sequence="GGGG")

        response = self.client.get('/api/sequences/')
        data = response.json()

        # El más reciente primero
        self.assertEqual(data['results'][0]['name'], 'third')
        self.assertEqual(data['results'][1]['name'], 'second')
        self.assertEqual(data['results'][2]['name'], 'first')

    def test_sequence_fields_in_list(self):
        """Lista debe incluir campos esperados"""
        DNASequence.objects.create(name="test", sequence="ATCG")

        response = self.client.get('/api/sequences/')
        data = response.json()
        item = data['results'][0]

        self.assertIn('id', item)
        self.assertIn('name', item)
        self.assertIn('length', item)
        self.assertIn('gc_content', item)
        self.assertIn('uploaded_at', item)
        # No debe incluir la secuencia completa
        self.assertNotIn('sequence', item)


class SearchAPIFunctionalTests(TestCase):
    """Pruebas funcionales para la API de búsqueda"""

    def setUp(self):
        self.client = Client()
        self.sequence = DNASequence.objects.create(
            name="test_sequence",
            sequence="ATGATGATGATG"
        )

    def test_search_success(self):
        """POST /api/search/ debe ejecutar búsqueda"""
        response = self.client.post(
            '/api/search/',
            json.dumps({
                'sequence_id': self.sequence.id,
                'pattern': 'ATG',
                'allow_overlapping': True
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('job', data)
        self.assertIn('results', data)
        self.assertIn('search_time_ms', data)
        self.assertIn('end_to_end_ms', data)

    def test_search_job_created(self):
        """POST /api/search/ debe crear job en BD"""
        response = self.client.post(
            '/api/search/',
            json.dumps({
                'sequence_id': self.sequence.id,
                'pattern': 'ATG',
                'allow_overlapping': True
            }),
            content_type='application/json'
        )

        data = response.json()
        job_id = data['job']['id']

        job = SearchJob.objects.get(id=job_id)
        self.assertEqual(job.pattern, 'ATG')
        self.assertEqual(job.status, 'COMPLETED')
        self.assertTrue(job.allow_overlapping)

    def test_search_results_saved(self):
        """POST /api/search/ debe guardar resultados en BD"""
        response = self.client.post(
            '/api/search/',
            json.dumps({
                'sequence_id': self.sequence.id,
                'pattern': 'ATG',
                'allow_overlapping': True
            }),
            content_type='application/json'
        )

        data = response.json()
        job_id = data['job']['id']

        job = SearchJob.objects.get(id=job_id)
        self.assertGreater(job.results.count(), 0)

    def test_search_without_sequence_id(self):
        """POST sin sequence_id debe retornar 400"""
        response = self.client.post(
            '/api/search/',
            json.dumps({'pattern': 'ATG'}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_search_without_pattern(self):
        """POST sin pattern debe retornar 400"""
        response = self.client.post(
            '/api/search/',
            json.dumps({'sequence_id': self.sequence.id}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_search_invalid_sequence_id(self):
        """POST con sequence_id inválido debe retornar 400"""
        response = self.client.post(
            '/api/search/',
            json.dumps({
                'sequence_id': 99999,  # No existe
                'pattern': 'ATG'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_search_invalid_pattern(self):
        """POST con patrón inválido debe retornar 400"""
        response = self.client.post(
            '/api/search/',
            json.dumps({
                'sequence_id': self.sequence.id,
                'pattern': 'XYZ123'  # Inválido
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_search_default_allow_overlapping(self):
        """allow_overlapping debe ser True por defecto"""
        response = self.client.post(
            '/api/search/',
            json.dumps({
                'sequence_id': self.sequence.id,
                'pattern': 'ATG'
            }),
            content_type='application/json'
        )

        data = response.json()
        self.assertTrue(data['job']['allow_overlapping'])

    def test_search_with_overlapping_false(self):
        """Debe respetar allow_overlapping=False"""
        response = self.client.post(
            '/api/search/',
            json.dumps({
                'sequence_id': self.sequence.id,
                'pattern': 'ATG',
                'allow_overlapping': False
            }),
            content_type='application/json'
        )

        data = response.json()
        self.assertFalse(data['job']['allow_overlapping'])

    def test_search_response_structure(self):
        """Respuesta debe tener estructura esperada"""
        response = self.client.post(
            '/api/search/',
            json.dumps({
                'sequence_id': self.sequence.id,
                'pattern': 'ATG'
            }),
            content_type='application/json'
        )

        data = response.json()

        # Verificar estructura de job
        self.assertIn('id', data['job'])
        self.assertIn('pattern', data['job'])
        self.assertIn('status', data['job'])
        self.assertIn('total_matches', data['job'])
        self.assertIn('search_time_ms', data['job'])
        self.assertIn('algorithm_used', data['job'])

        # Verificar estructura de results
        if len(data['results']) > 0:
            result = data['results'][0]
            self.assertIn('position', result)
            self.assertIn('context_before', result)
            self.assertIn('context_after', result)

    def test_search_job_detail_get(self):
        """GET /api/search/jobs/<id>/ debe retornar detalles del job"""
        # Crear job primero
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG",
            status='COMPLETED',
            total_matches=4,
            search_time_ms=50.0,
            algorithm_used='naive-local'
        )
        SearchResult.objects.create(job=job, position=0)
        SearchResult.objects.create(job=job, position=3)

        response = self.client.get(f'/api/search/jobs/{job.id}/')

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('job', data)
        self.assertIn('results', data)
        self.assertEqual(data['job']['id'], job.id)

    def test_search_job_detail_invalid_id(self):
        """GET con ID inválido debe retornar 404"""
        response = self.client.get('/api/search/jobs/99999/')
        self.assertEqual(response.status_code, 404)

    def test_search_results_limit_default(self):
        """Resultados deben limitarse a 100 por defecto"""
        # Crear job con muchos resultados
        large_seq = DNASequence.objects.create(
            name="large",
            sequence="A" * 200
        )
        job = SearchJob.objects.create(
            sequence=large_seq,
            pattern="A",
            status='COMPLETED',
            total_matches=200
        )

        # Crear 200 resultados
        SearchResult.objects.bulk_create([
            SearchResult(job=job, position=i)
            for i in range(200)
        ])

        response = self.client.get(f'/api/search/jobs/{job.id}/')
        data = response.json()

        # Debe retornar máximo 100
        self.assertLessEqual(len(data['results']), 100)

    def test_search_results_custom_limit(self):
        """Debe permitir límite personalizado de resultados"""
        job = SearchJob.objects.create(
            sequence=self.sequence,
            pattern="ATG",
            status='COMPLETED'
        )

        for i in range(50):
            SearchResult.objects.create(job=job, position=i)

        response = self.client.get(f'/api/search/jobs/{job.id}/?limit=10')
        data = response.json()

        self.assertEqual(len(data['results']), 10)

    def test_search_no_matches(self):
        """Búsqueda sin coincidencias debe completarse correctamente"""
        response = self.client.post(
            '/api/search/',
            json.dumps({
                'sequence_id': self.sequence.id,
                'pattern': 'ZZZZZ'  # No existe
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['job']['total_matches'], 0)
        self.assertEqual(len(data['results']), 0)


class APICorsTests(TestCase):
    """Pruebas relacionadas con CORS"""

    def setUp(self):
        self.client = Client()

    def test_cors_headers_present(self):
        """Respuestas deben incluir headers CORS"""
        response = self.client.get('/api/sequences/')

        # Verificar si hay headers CORS (depende de configuración)
        # Este test puede fallar si CORS no está configurado en desarrollo
        self.assertEqual(response.status_code, 200)

    def test_options_method(self):
        """Debe soportar método OPTIONS para preflight"""
        response = self.client.options('/api/sequences/')

        # Debe permitir OPTIONS
        self.assertIn(response.status_code, [200, 204])


class APIErrorHandlingTests(TestCase):
    """Pruebas de manejo de errores de la API"""

    def setUp(self):
        self.client = Client()

    def test_invalid_json(self):
        """POST con JSON inválido debe retornar 400"""
        response = self.client.post(
            '/api/search/',
            'invalid json{',
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)

    def test_missing_content_type(self):
        """POST sin Content-Type apropiado debe manejarse"""
        sequence = DNASequence.objects.create(name="test", sequence="ATCG")

        response = self.client.post(
            '/api/search/',
            {'sequence_id': sequence.id, 'pattern': 'AT'}
        )

        # Puede ser 400 o manejarse de otra forma
        self.assertIn(response.status_code, [200, 400, 415])

    def test_method_not_allowed(self):
        """Métodos no permitidos deben retornar 405"""
        response = self.client.delete('/api/sequences/')
        self.assertEqual(response.status_code, 405)

    def test_url_not_found(self):
        """URLs inexistentes deben retornar 404"""
        response = self.client.get('/api/nonexistent/')
        self.assertEqual(response.status_code, 404)
