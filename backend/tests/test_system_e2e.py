"""
Pruebas del sistema (End-to-End)

Cubre:
- Flujos completos de usuario
- Interacción entre múltiples componentes
- Escenarios de uso real
- Validación de funcionalidad completa
"""

import io
import json
from django.test import TestCase, Client

from sequences_api.models import DNASequence
from search_api.models import SearchJob, SearchResult


class UploadAndSearchE2ETest(TestCase):
    """Prueba E2E: Upload de secuencia + Búsqueda de patrón"""

    def setUp(self):
        self.client = Client()

    def create_mock_file(self, content, filename="test.txt"):
        """Helper para crear archivos mock"""
        file_obj = io.BytesIO(content.encode('utf-8'))
        file_obj.name = filename
        return file_obj

    def test_complete_user_flow(self):
        """
        Flujo completo:
        1. Usuario sube secuencia
        2. Sistema la procesa y guarda
        3. Usuario ejecuta búsqueda
        4. Sistema encuentra coincidencias
        5. Usuario consulta resultados
        """
        # 1. Upload sequence
        sequence_content = "ATGATGATGATG"
        file_obj = self.create_mock_file(sequence_content, "my_dna.txt")

        upload_response = self.client.post(
            '/api/sequences/upload/',
            {'file': file_obj, 'name': 'my_dna_sequence'},
            format='multipart'
        )

        self.assertEqual(upload_response.status_code, 201)
        sequence_data = upload_response.json()
        sequence_id = sequence_data['id']

        # Verificar en BD
        self.assertTrue(DNASequence.objects.filter(id=sequence_id).exists())

        # 2. List sequences para verificar
        list_response = self.client.get('/api/sequences/')
        self.assertEqual(list_response.status_code, 200)
        sequences = list_response.json()['results']
        self.assertEqual(len(sequences), 1)
        self.assertEqual(sequences[0]['name'], 'my_dna_sequence')

        # 3. Ejecutar búsqueda
        search_response = self.client.post(
            '/api/search/',
            json.dumps({
                'sequence_id': sequence_id,
                'pattern': 'ATG',
                'allow_overlapping': True
            }),
            content_type='application/json'
        )

        self.assertEqual(search_response.status_code, 200)
        search_data = search_response.json()
        job_id = search_data['job']['id']

        # Verificar resultados inmediatos
        self.assertEqual(search_data['job']['status'], 'COMPLETED')
        self.assertGreater(search_data['job']['total_matches'], 0)
        self.assertGreater(len(search_data['results']), 0)

        # 4. Consultar detalles del job
        job_detail_response = self.client.get(f'/api/search/jobs/{job_id}/')
        self.assertEqual(job_detail_response.status_code, 200)

        job_detail = job_detail_response.json()
        self.assertEqual(job_detail['job']['pattern'], 'ATG')
        self.assertGreater(len(job_detail['results']), 0)

        # Verificar estructura de resultados
        result = job_detail['results'][0]
        self.assertIn('position', result)
        self.assertIn('context_before', result)
        self.assertIn('context_after', result)

    def test_multiple_searches_same_sequence(self):
        """
        Usuario puede ejecutar múltiples búsquedas en la misma secuencia
        """
        # Upload sequence
        file_obj = self.create_mock_file("ATGATGATGATG", "seq.txt")
        upload_response = self.client.post(
            '/api/sequences/upload/',
            {'file': file_obj},
            format='multipart'
        )
        sequence_id = upload_response.json()['id']

        # Búsqueda 1: ATG
        search1 = self.client.post(
            '/api/search/',
            json.dumps({'sequence_id': sequence_id, 'pattern': 'ATG'}),
            content_type='application/json'
        )
        self.assertEqual(search1.status_code, 200)

        # Búsqueda 2: TGA
        search2 = self.client.post(
            '/api/search/',
            json.dumps({'sequence_id': sequence_id, 'pattern': 'TGA'}),
            content_type='application/json'
        )
        self.assertEqual(search2.status_code, 200)

        # Búsqueda 3: GAT
        search3 = self.client.post(
            '/api/search/',
            json.dumps({'sequence_id': sequence_id, 'pattern': 'GAT'}),
            content_type='application/json'
        )
        self.assertEqual(search3.status_code, 200)

        # Verificar que se crearon 3 jobs
        self.assertEqual(SearchJob.objects.filter(sequence_id=sequence_id).count(), 3)

    def test_upload_fasta_and_search(self):
        """
        Flujo con formato FASTA
        """
        fasta_content = ">my_sequence\nATCGATCGATCG\nATCGATCG"
        file_obj = self.create_mock_file(fasta_content, "seq.fasta")

        upload_response = self.client.post(
            '/api/sequences/upload/',
            {'file': file_obj},
            format='multipart'
        )

        self.assertEqual(upload_response.status_code, 201)
        sequence_id = upload_response.json()['id']

        # Búsqueda
        search_response = self.client.post(
            '/api/search/',
            json.dumps({'sequence_id': sequence_id, 'pattern': 'TCG'}),
            content_type='application/json'
        )

        self.assertEqual(search_response.status_code, 200)
        self.assertGreater(search_response.json()['job']['total_matches'], 0)

    def test_duplicate_upload_workflow(self):
        """
        Subir duplicado debe retornar la secuencia existente
        """
        content = "ATCGATCG"

        # Primera carga
        file1 = self.create_mock_file(content, "file1.txt")
        response1 = self.client.post(
            '/api/sequences/upload/',
            {'file': file1},
            format='multipart'
        )
        self.assertEqual(response1.status_code, 201)
        id1 = response1.json()['id']

        # Segunda carga (duplicado)
        file2 = self.create_mock_file(content, "file2.txt")
        response2 = self.client.post(
            '/api/sequences/upload/',
            {'file': file2},
            format='multipart'
        )
        self.assertEqual(response2.status_code, 200)  # No 201
        id2 = response2.json()['id']

        # Debe ser el mismo ID
        self.assertEqual(id1, id2)

        # Solo debe haber 1 secuencia en BD
        self.assertEqual(DNASequence.objects.count(), 1)


class MultipleSequencesE2ETest(TestCase):
    """Pruebas E2E con múltiples secuencias"""

    def setUp(self):
        self.client = Client()

    def create_mock_file(self, content, filename="test.txt"):
        file_obj = io.BytesIO(content.encode('utf-8'))
        file_obj.name = filename
        return file_obj

    def test_upload_multiple_sequences_and_search_each(self):
        """
        Usuario sube múltiples secuencias y busca en cada una
        """
        sequences = [
            ("seq1.txt", "ATGATGATG"),
            ("seq2.txt", "GGGGGG"),
            ("seq3.txt", "CCCCCC"),
        ]

        sequence_ids = []

        # Upload todas
        for filename, content in sequences:
            file_obj = self.create_mock_file(content, filename)
            response = self.client.post(
                '/api/sequences/upload/',
                {'file': file_obj},
                format='multipart'
            )
            self.assertEqual(response.status_code, 201)
            sequence_ids.append(response.json()['id'])

        # Verificar lista
        list_response = self.client.get('/api/sequences/')
        self.assertEqual(len(list_response.json()['results']), 3)

        # Buscar en cada una
        for seq_id in sequence_ids:
            search_response = self.client.post(
                '/api/search/',
                json.dumps({'sequence_id': seq_id, 'pattern': 'ATG'}),
                content_type='application/json'
            )
            self.assertEqual(search_response.status_code, 200)

    def test_pagination_with_many_sequences(self):
        """
        Con muchas secuencias, la paginación debe funcionar
        """
        # Crear 25 secuencias
        for i in range(25):
            file_obj = self.create_mock_file(f"ATCG{i}", f"seq{i}.txt")
            self.client.post(
                '/api/sequences/upload/',
                {'file': file_obj},
                format='multipart'
            )

        # Página 1
        page1 = self.client.get('/api/sequences/').json()
        self.assertEqual(len(page1['results']), 20)
        self.assertIsNotNone(page1['next'])

        # Página 2
        page2 = self.client.get('/api/sequences/?page=2').json()
        self.assertEqual(len(page2['results']), 5)


class ErrorRecoveryE2ETest(TestCase):
    """Pruebas E2E de manejo de errores"""

    def setUp(self):
        self.client = Client()

    def create_mock_file(self, content, filename="test.txt"):
        file_obj = io.BytesIO(content.encode('utf-8'))
        file_obj.name = filename
        return file_obj

    def test_invalid_upload_then_valid_upload(self):
        """
        Usuario intenta upload inválido, luego uno válido
        """
        # Intento 1: Inválido
        invalid_file = self.create_mock_file("ATCG123XYZ")
        response1 = self.client.post(
            '/api/sequences/upload/',
            {'file': invalid_file},
            format='multipart'
        )
        self.assertEqual(response1.status_code, 400)

        # Intento 2: Válido
        valid_file = self.create_mock_file("ATCGATCG")
        response2 = self.client.post(
            '/api/sequences/upload/',
            {'file': valid_file},
            format='multipart'
        )
        self.assertEqual(response2.status_code, 201)

        # Solo debe haber 1 secuencia
        self.assertEqual(DNASequence.objects.count(), 1)

    def test_search_nonexistent_sequence(self):
        """
        Búsqueda en secuencia inexistente debe fallar correctamente
        """
        response = self.client.post(
            '/api/search/',
            json.dumps({'sequence_id': 99999, 'pattern': 'ATG'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_search_invalid_pattern_then_valid(self):
        """
        Usuario busca con patrón inválido, luego con uno válido
        """
        # Crear secuencia
        file_obj = self.create_mock_file("ATCGATCG")
        upload_response = self.client.post(
            '/api/sequences/upload/',
            {'file': file_obj},
            format='multipart'
        )
        sequence_id = upload_response.json()['id']

        # Búsqueda inválida
        response1 = self.client.post(
            '/api/search/',
            json.dumps({'sequence_id': sequence_id, 'pattern': 'XYZ123'}),
            content_type='application/json'
        )
        self.assertEqual(response1.status_code, 400)

        # Búsqueda válida
        response2 = self.client.post(
            '/api/search/',
            json.dumps({'sequence_id': sequence_id, 'pattern': 'ATG'}),
            content_type='application/json'
        )
        self.assertEqual(response2.status_code, 200)


class DataConsistencyE2ETest(TestCase):
    """Pruebas E2E de consistencia de datos"""

    def setUp(self):
        self.client = Client()

    def create_mock_file(self, content, filename="test.txt"):
        file_obj = io.BytesIO(content.encode('utf-8'))
        file_obj.name = filename
        return file_obj

    def test_search_results_match_sequence(self):
        """
        Resultados de búsqueda deben coincidir con la secuencia real
        """
        sequence_content = "ATGATGATGATG"
        file_obj = self.create_mock_file(sequence_content)

        upload_response = self.client.post(
            '/api/sequences/upload/',
            {'file': file_obj},
            format='multipart'
        )
        sequence_id = upload_response.json()['id']

        search_response = self.client.post(
            '/api/search/',
            json.dumps({'sequence_id': sequence_id, 'pattern': 'ATG'}),
            content_type='application/json'
        )

        search_data = search_response.json()

        # Verificar que las posiciones son correctas
        sequence = DNASequence.objects.get(id=sequence_id)
        for result in search_data['results']:
            position = result['position']
            actual_substring = sequence.sequence[position:position+3]
            self.assertEqual(actual_substring, 'ATG')

    def test_gc_content_accuracy(self):
        """
        GC content calculado debe ser preciso
        """
        test_cases = [
            ("ATCG", 50.0),  # 2/4 = 50%
            ("AAAA", 0.0),   # 0/4 = 0%
            ("GGCC", 100.0), # 4/4 = 100%
            ("ATCGATCG", 50.0), # 4/8 = 50%
        ]

        for content, expected_gc in test_cases:
            file_obj = self.create_mock_file(content)
            response = self.client.post(
                '/api/sequences/upload/',
                {'file': file_obj},
                format='multipart'
            )
            self.assertEqual(response.json()['gc_content'], expected_gc)

    def test_search_metrics_consistency(self):
        """
        Métricas de búsqueda deben ser consistentes
        """
        file_obj = self.create_mock_file("ATGATGATG")
        upload_response = self.client.post(
            '/api/sequences/upload/',
            {'file': file_obj},
            format='multipart'
        )
        sequence_id = upload_response.json()['id']

        search_response = self.client.post(
            '/api/search/',
            json.dumps({'sequence_id': sequence_id, 'pattern': 'ATG'}),
            content_type='application/json'
        )

        data = search_response.json()

        # Total matches debe coincidir con número de resultados
        total_matches = data['job']['total_matches']
        actual_results = len(data['results'])

        # Pueden no ser iguales si hay más de 100 resultados (límite)
        if total_matches <= 100:
            self.assertEqual(total_matches, actual_results)

        # Search time debe ser > 0
        self.assertGreater(data['job']['search_time_ms'], 0)
        self.assertGreater(data['end_to_end_ms'], 0)
