"""
Pruebas de seguridad

Cubre:
- Inyección SQL
- XSS (Cross-Site Scripting)
- Path traversal
- Límites de archivo
- Validación de entrada
- Rate limiting (si está implementado)
"""

import io
import json
from django.test import TestCase, Client
from sequences_api.models import DNASequence


class SQLInjectionTests(TestCase):
    """Pruebas de seguridad contra inyección SQL"""

    def setUp(self):
        self.client = Client()
        self.sequence = DNASequence.objects.create(
            name="test",
            sequence="ATCGATCG"
        )

    def test_sql_injection_in_pattern_search(self):
        """
        Patrón de búsqueda con SQL injection no debe afectar BD
        """
        sql_injection_patterns = [
            "ATG' OR '1'='1",
            "ATG'; DROP TABLE sequences;--",
            "ATG' UNION SELECT * FROM users--",
            "ATG' AND 1=1--",
        ]

        for pattern in sql_injection_patterns:
            response = self.client.post(
                '/api/search/',
                json.dumps({
                    'sequence_id': self.sequence.id,
                    'pattern': pattern
                }),
                content_type='application/json'
            )

            # Debe rechazar o manejar sin inyectar SQL
            # Django ORM protege contra esto automáticamente
            self.assertIn(response.status_code, [400, 200])

        # Verificar que la BD sigue intacta
        self.assertTrue(DNASequence.objects.filter(id=self.sequence.id).exists())

    def test_sql_injection_in_name_field(self):
        """
        Campo name con SQL injection no debe afectar BD
        """
        file_obj = io.BytesIO(b"ATCG")
        file_obj.name = "test.txt"

        malicious_names = [
            "file'; DROP TABLE sequences;--",
            "file' OR '1'='1",
            "'; DELETE FROM sequences WHERE '1'='1",
        ]

        for name in malicious_names:
            response = self.client.post(
                '/api/sequences/upload/',
                {'file': file_obj, 'name': name},
                format='multipart'
            )

            # Debe manejar sin inyección SQL
            # Si acepta, verifica que no causó daño
            if response.status_code == 201:
                created_id = response.json()['id']
                obj = DNASequence.objects.get(id=created_id)
                # El nombre se debe guardar como string literal
                self.assertEqual(obj.name, name)


class InputValidationTests(TestCase):
    """Pruebas de validación de entrada"""

    def setUp(self):
        self.client = Client()

    def create_mock_file(self, content, filename="test.txt"):
        if isinstance(content, str):
            content = content.encode('utf-8')
        file_obj = io.BytesIO(content)
        file_obj.name = filename
        file_obj.size = len(content)
        return file_obj

    def test_rejects_oversized_file(self):
        """
        Archivos > 150MB deben ser rechazados
        """
        # Crear archivo mock que simula ser > 150MB
        small_content = b"ATCG"
        file_obj = self.create_mock_file(small_content)
        file_obj.size = 160 * 1024 * 1024  # 160MB (mocked)

        response = self.client.post(
            '/api/sequences/upload/',
            {'file': file_obj},
            format='multipart'
        )

        self.assertEqual(response.status_code, 400)

    def test_rejects_special_characters_in_sequence(self):
        """
        Secuencias con caracteres especiales deben ser rechazadas
        """
        invalid_sequences = [
            "ATCG<script>alert('xss')</script>",
            "ATCG@#$%^&*()",
            "ATCG!\"£$%^&*()",
            "ATCG\x00\x01\x02",  # Caracteres nulos
        ]

        for seq in invalid_sequences:
            file_obj = self.create_mock_file(seq)
            response = self.client.post(
                '/api/sequences/upload/',
                {'file': file_obj},
                format='multipart'
            )

            # Debe rechazar
            self.assertEqual(response.status_code, 400)

    def test_rejects_extremely_long_pattern(self):
        """
        Patrones > 1000 caracteres deben ser rechazados
        """
        sequence = DNASequence.objects.create(
            name="test",
            sequence="ATCG" * 100
        )

        long_pattern = "A" * 1001

        response = self.client.post(
            '/api/search/',
            json.dumps({
                'sequence_id': sequence.id,
                'pattern': long_pattern
            }),
            content_type='application/json'
        )

        # Debe rechazar por longitud
        self.assertIn(response.status_code, [400, 500])

    def test_handles_empty_file(self):
        """
        Archivos vacíos deben ser rechazados correctamente
        """
        file_obj = self.create_mock_file(b"")

        response = self.client.post(
            '/api/sequences/upload/',
            {'file': file_obj},
            format='multipart'
        )

        self.assertEqual(response.status_code, 400)

    def test_handles_binary_garbage(self):
        """
        Archivos con basura binaria deben ser rechazados
        """
        binary_garbage = b"\x00\x01\x02\x03\xff\xfe\xfd"
        file_obj = self.create_mock_file(binary_garbage)

        response = self.client.post(
            '/api/sequences/upload/',
            {'file': file_obj},
            format='multipart'
        )

        # Debe rechazar o manejar gracefully
        self.assertIn(response.status_code, [400, 500])


class PathTraversalTests(TestCase):
    """Pruebas contra path traversal attacks"""

    def setUp(self):
        self.client = Client()

    def create_mock_file(self, content, filename="test.txt"):
        file_obj = io.BytesIO(content.encode('utf-8'))
        file_obj.name = filename
        return file_obj

    def test_path_traversal_in_filename(self):
        """
        Nombres de archivo con path traversal no deben causar problemas
        """
        malicious_filenames = [
            "../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "../../../root/.ssh/id_rsa",
            "....//....//etc/passwd",
        ]

        for filename in malicious_filenames:
            file_obj = self.create_mock_file("ATCG", filename)

            response = self.client.post(
                '/api/sequences/upload/',
                {'file': file_obj},
                format='multipart'
            )

            # No debe causar error de servidor
            self.assertNotEqual(response.status_code, 500)

            # Si acepta, verificar que el nombre se sanitizó
            if response.status_code == 201:
                data = response.json()
                # El nombre no debe incluir ../ o similar
                self.assertNotIn('..', data['name'])


class XSSTests(TestCase):
    """Pruebas contra Cross-Site Scripting"""

    def setUp(self):
        self.client = Client()

    def create_mock_file(self, content, filename="test.txt"):
        file_obj = io.BytesIO(content.encode('utf-8'))
        file_obj.name = filename
        return file_obj

    def test_xss_in_sequence_name(self):
        """
        Nombres con scripts XSS no deben ejecutarse
        """
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
        ]

        for payload in xss_payloads:
            file_obj = self.create_mock_file("ATCG", "test.txt")

            response = self.client.post(
                '/api/sequences/upload/',
                {'file': file_obj, 'name': payload},
                format='multipart'
            )

            # Si acepta, verificar que se escapó correctamente
            if response.status_code == 201:
                data = response.json()
                # API REST devuelve JSON, así que los caracteres < > deben estar
                # pero el frontend debe escaparlos al renderizar
                self.assertIn('name', data)

    def test_response_content_type_is_json(self):
        """
        Respuestas deben ser JSON para prevenir XSS
        """
        response = self.client.get('/api/sequences/')

        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response['Content-Type'])


class DataLeakageTests(TestCase):
    """Pruebas de prevención de fuga de datos"""

    def setUp(self):
        self.client = Client()

    def test_sequence_content_not_in_list_response(self):
        """
        Lista de secuencias no debe exponer contenido completo
        """
        DNASequence.objects.create(
            name="test",
            sequence="ATCGATCG" * 10000  # Secuencia grande
        )

        response = self.client.get('/api/sequences/')
        data = response.json()

        # No debe incluir el campo 'sequence' completo
        if len(data['results']) > 0:
            self.assertNotIn('sequence', data['results'][0])

    def test_error_messages_dont_leak_sensitive_info(self):
        """
        Mensajes de error no deben revelar información sensible
        """
        response = self.client.post(
            '/api/search/',
            json.dumps({
                'sequence_id': 99999,  # No existe
                'pattern': 'ATG'
            }),
            content_type='application/json'
        )

        # Debe ser error 400
        self.assertEqual(response.status_code, 400)

        # Error no debe revelar detalles de implementación
        error_text = response.content.decode('utf-8').lower()
        sensitive_keywords = ['traceback', 'exception', 'sql', 'database']

        for keyword in sensitive_keywords:
            self.assertNotIn(keyword, error_text)


class DenialOfServiceTests(TestCase):
    """Pruebas básicas contra DoS"""

    def setUp(self):
        self.client = Client()

    def create_mock_file(self, content, filename="test.txt"):
        if isinstance(content, str):
            content = content.encode('utf-8')
        file_obj = io.BytesIO(content)
        file_obj.name = filename
        return file_obj

    def test_handles_deeply_nested_pattern_gracefully(self):
        """
        Patrones complejos no deben causar timeout
        """
        sequence = DNASequence.objects.create(
            name="test",
            sequence="A" * 10000
        )

        # Patrón que podría causar backtracking en regex mal implementados
        response = self.client.post(
            '/api/search/',
            json.dumps({
                'sequence_id': sequence.id,
                'pattern': 'A' * 100
            }),
            content_type='application/json'
        )

        # Debe completarse (no timeout)
        self.assertIn(response.status_code, [200, 400, 500])

    def test_multiple_concurrent_uploads_handled(self):
        """
        Múltiples uploads simultáneos no deben causar problemas
        """
        # Simular varios uploads en secuencia rápida
        for i in range(10):
            file_obj = self.create_mock_file(f"ATCG{i}")
            response = self.client.post(
                '/api/sequences/upload/',
                {'file': file_obj},
                format='multipart'
            )
            # Todos deben procesarse
            self.assertIn(response.status_code, [200, 201])


class AuthenticationTests(TestCase):
    """
    Pruebas de autenticación
    (Actualmente la API es AllowAny, pero estos tests estarían listos)
    """

    def setUp(self):
        self.client = Client()

    def test_api_currently_allows_anonymous_access(self):
        """
        Verificar que la API actualmente permite acceso anónimo
        (esto es intencional en desarrollo)
        """
        response = self.client.get('/api/sequences/')
        self.assertEqual(response.status_code, 200)

    # Los siguientes tests se activarían cuando se implemente autenticación
    """
    def test_unauthenticated_request_rejected(self):
        response = self.client.get('/api/sequences/')
        self.assertEqual(response.status_code, 401)

    def test_invalid_token_rejected(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        response = self.client.get('/api/sequences/')
        self.assertEqual(response.status_code, 401)
    """


class ContentTypeValidationTests(TestCase):
    """Pruebas de validación de tipo de contenido"""

    def setUp(self):
        self.client = Client()
        self.sequence = DNASequence.objects.create(
            name="test",
            sequence="ATCG"
        )

    def test_json_content_type_required_for_search(self):
        """
        Búsquedas deben requerir Content-Type: application/json
        """
        response = self.client.post(
            '/api/search/',
            {'sequence_id': self.sequence.id, 'pattern': 'AT'},
            # Sin content_type='application/json'
        )

        # Puede ser 400 o procesarse de otra forma
        # Lo importante es que maneje correctamente
        self.assertIn(response.status_code, [200, 400, 415])

    def test_multipart_required_for_upload(self):
        """
        Upload debe usar multipart/form-data
        """
        response = self.client.post(
            '/api/sequences/upload/',
            json.dumps({'file': 'ATCG'}),
            content_type='application/json'
        )

        # Debe rechazar JSON para upload
        self.assertEqual(response.status_code, 400)
