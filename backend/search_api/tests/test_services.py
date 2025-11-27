"""
Pruebas unitarias para search_api/services.py

Cubre:
- run_local_search
- run_grpc_search
- run_search (orquestación)
- Búsqueda con/sin solapamiento
- Cálculo de contexto
- Manejo de errores
"""

from unittest.mock import Mock, patch
from django.test import TestCase, override_settings
from rest_framework.serializers import ValidationError
import grpc

from search_api.services import (
    _find_matches,
    run_local_search,
    run_grpc_search,
    run_search
)


class FindMatchesTests(TestCase):
    """Pruebas para la función interna _find_matches"""

    def test_simple_match(self):
        """Debe encontrar coincidencia simple"""
        matches = _find_matches("ATCGATCG", "TCG", allow_overlapping=True)
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0]['position'], 1)
        self.assertEqual(matches[1]['position'], 5)

    def test_no_matches(self):
        """Debe devolver lista vacía si no hay coincidencias"""
        matches = _find_matches("AAAA", "TTT", allow_overlapping=True)
        self.assertEqual(len(matches), 0)

    def test_overlapping_matches(self):
        """Debe encontrar coincidencias solapadas"""
        matches = _find_matches("AAAA", "AA", allow_overlapping=True)
        self.assertEqual(len(matches), 3)  # Posiciones 0, 1, 2

    def test_non_overlapping_matches(self):
        """Debe encontrar solo coincidencias no solapadas"""
        matches = _find_matches("AAAA", "AA", allow_overlapping=False)
        self.assertEqual(len(matches), 2)  # Posiciones 0, 2

    def test_context_before(self):
        """Debe capturar contexto antes de la coincidencia"""
        matches = _find_matches("0123456789ATCG", "ATCG", allow_overlapping=True)
        self.assertEqual(matches[0]['context_before'], "0123456789")

    def test_context_after(self):
        """Debe capturar contexto después de la coincidencia"""
        matches = _find_matches("ATCG0123456789", "ATCG", allow_overlapping=True)
        self.assertEqual(matches[0]['context_after'], "0123456789")

    def test_context_before_at_start(self):
        """Contexto antes debe estar vacío si coincidencia está al inicio"""
        matches = _find_matches("ATCG", "ATCG", allow_overlapping=True)
        self.assertEqual(matches[0]['context_before'], "")

    def test_context_after_at_end(self):
        """Contexto después debe estar vacío si coincidencia está al final"""
        matches = _find_matches("ATCG", "ATCG", allow_overlapping=True)
        self.assertEqual(matches[0]['context_after'], "")

    def test_context_limited_to_10_chars(self):
        """Contexto debe limitarse a 10 caracteres"""
        long_seq = "A" * 20 + "ATCG" + "T" * 20
        matches = _find_matches(long_seq, "ATCG", allow_overlapping=True)
        self.assertEqual(len(matches[0]['context_before']), 10)
        self.assertEqual(len(matches[0]['context_after']), 10)

    def test_pattern_longer_than_sequence(self):
        """Patrón más largo que secuencia debe devolver vacío"""
        matches = _find_matches("AT", "ATCGATCG", allow_overlapping=True)
        self.assertEqual(len(matches), 0)

    def test_multiple_non_overlapping_matches(self):
        """Debe encontrar múltiples coincidencias no solapadas"""
        matches = _find_matches("ATGATGATG", "ATG", allow_overlapping=False)
        self.assertEqual(len(matches), 3)
        self.assertEqual(matches[0]['position'], 0)
        self.assertEqual(matches[1]['position'], 3)
        self.assertEqual(matches[2]['position'], 6)


class RunLocalSearchTests(TestCase):
    """Pruebas para run_local_search"""

    def test_basic_search(self):
        """Debe ejecutar búsqueda local básica"""
        result = run_local_search("ATCGATCG", "TCG", allow_overlapping=True)

        self.assertEqual(result['pattern'], "TCG")
        self.assertEqual(result['total_matches'], 2)
        self.assertGreater(result['search_time_ms'], 0)
        self.assertEqual(result['algorithm_used'], "naive-local")
        self.assertEqual(len(result['matches']), 2)

    def test_normalizes_pattern(self):
        """Debe normalizar patrón (minúsculas a mayúsculas)"""
        result = run_local_search("ATCGATCG", "tcg", allow_overlapping=True)
        self.assertEqual(result['pattern'], "TCG")

    def test_validates_pattern(self):
        """Debe validar patrón de ADN"""
        with self.assertRaises(ValidationError):
            run_local_search("ATCGATCG", "XYZ123", allow_overlapping=True)

    def test_rejects_long_pattern(self):
        """Debe rechazar patrones > 1000 caracteres"""
        long_pattern = "A" * 1001
        with self.assertRaises(ValueError) as context:
            run_local_search("ATCGATCG", long_pattern, allow_overlapping=True)
        self.assertIn("demasiado largo", str(context.exception))

    def test_search_time_measurement(self):
        """Debe medir tiempo de búsqueda"""
        result = run_local_search("ATCG" * 1000, "ATG", allow_overlapping=True)
        self.assertIsInstance(result['search_time_ms'], float)
        self.assertGreater(result['search_time_ms'], 0)

    def test_overlapping_parameter(self):
        """Debe respetar parámetro allow_overlapping"""
        seq = "AAAA"
        pat = "AA"

        result_overlap = run_local_search(seq, pat, allow_overlapping=True)
        self.assertEqual(result_overlap['total_matches'], 3)

        result_no_overlap = run_local_search(seq, pat, allow_overlapping=False)
        self.assertEqual(result_no_overlap['total_matches'], 2)

    def test_empty_pattern_after_normalization(self):
        """Debe rechazar patrón vacío después de normalización"""
        with self.assertRaises(ValidationError):
            run_local_search("ATCG", "   ", allow_overlapping=True)


class RunGrpcSearchTests(TestCase):
    """Pruebas para run_grpc_search"""

    @patch('search_api.services.get_grpc_client')
    def test_successful_grpc_search(self, mock_get_client):
        """Debe ejecutar búsqueda gRPC exitosamente"""
        # Mock response
        mock_match = Mock()
        mock_match.position = 5
        mock_match.context_before = "ATCGA"
        mock_match.context_after = "ATCG"

        mock_response = Mock()
        mock_response.matches = [mock_match]
        mock_response.total_matches = 1
        mock_response.search_time_ms = 42.5
        mock_response.algorithm_used = "KMP"

        mock_client = Mock()
        mock_client.search.return_value = mock_response
        mock_client.address = "localhost:50051"
        mock_get_client.return_value = mock_client

        result = run_grpc_search("ATCGATCGATCG", "ATG", allow_overlapping=True)

        self.assertEqual(result['pattern'], "ATG")
        self.assertEqual(result['total_matches'], 1)
        self.assertEqual(result['search_time_ms'], 42.5)
        self.assertEqual(result['algorithm_used'], "KMP")
        self.assertEqual(len(result['matches']), 1)
        self.assertEqual(result['matches'][0]['position'], 5)

    @patch('search_api.services.get_grpc_client')
    def test_grpc_normalizes_pattern(self, mock_get_client):
        """Debe normalizar patrón antes de enviar a gRPC"""
        mock_response = Mock()
        mock_response.matches = []
        mock_response.total_matches = 0
        mock_response.search_time_ms = 10.0
        mock_response.algorithm_used = "KMP"

        mock_client = Mock()
        mock_client.search.return_value = mock_response
        mock_client.address = "localhost:50051"
        mock_get_client.return_value = mock_client

        run_grpc_search("ATCG", "atg", allow_overlapping=True)

        # Verificar que se llamó con patrón normalizado
        call_args = mock_client.search.call_args
        self.assertEqual(call_args[1]['pattern'], "ATG")

    @patch('search_api.services.get_grpc_client')
    def test_grpc_passes_allow_overlapping(self, mock_get_client):
        """Debe pasar parámetro allow_overlapping a gRPC"""
        mock_response = Mock()
        mock_response.matches = []
        mock_response.total_matches = 0
        mock_response.search_time_ms = 10.0
        mock_response.algorithm_used = "KMP"

        mock_client = Mock()
        mock_client.search.return_value = mock_response
        mock_client.address = "localhost:50051"
        mock_get_client.return_value = mock_client

        run_grpc_search("ATCG", "AT", allow_overlapping=False)

        call_args = mock_client.search.call_args
        self.assertEqual(call_args[1]['allow_overlapping'], False)

    @patch('search_api.services.get_grpc_client')
    def test_grpc_multiple_matches(self, mock_get_client):
        """Debe manejar múltiples coincidencias de gRPC"""
        mock_matches = [
            Mock(position=0, context_before="", context_after="ATCG"),
            Mock(position=5, context_before="ATCGA", context_after=""),
        ]

        mock_response = Mock()
        mock_response.matches = mock_matches
        mock_response.total_matches = 2
        mock_response.search_time_ms = 50.0
        mock_response.algorithm_used = "KMP"

        mock_client = Mock()
        mock_client.search.return_value = mock_response
        mock_client.address = "localhost:50051"
        mock_get_client.return_value = mock_client

        result = run_grpc_search("ATCGATCGATCG", "ATG", allow_overlapping=True)

        self.assertEqual(len(result['matches']), 2)
        self.assertEqual(result['total_matches'], 2)


class RunSearchOrchestrationTests(TestCase):
    """Pruebas para run_search (orquestación)"""

    @override_settings(USE_GRPC_SEARCH=False)
    def test_uses_local_when_grpc_disabled(self):
        """Debe usar búsqueda local cuando gRPC está deshabilitado"""
        result = run_search("ATCGATCG", "TCG", allow_overlapping=True)
        self.assertEqual(result['algorithm_used'], "naive-local")

    @override_settings(USE_GRPC_SEARCH=True)
    @patch('search_api.services.run_grpc_search')
    def test_uses_grpc_when_enabled(self, mock_grpc_search):
        """Debe usar gRPC cuando está habilitado"""
        mock_grpc_search.return_value = {
            'pattern': 'ATG',
            'total_matches': 1,
            'search_time_ms': 20.0,
            'matches': [],
            'algorithm_used': 'KMP'
        }

        result = run_search("ATCGATCG", "ATG", allow_overlapping=True)

        mock_grpc_search.assert_called_once()
        self.assertEqual(result['algorithm_used'], 'KMP')

    @override_settings(USE_GRPC_SEARCH=True)
    @patch('search_api.services.run_grpc_search')
    @patch('search_api.services.run_local_search')
    def test_fallback_to_local_on_grpc_error(self, mock_local, mock_grpc):
        """Debe hacer fallback a local si gRPC falla"""
        mock_grpc.side_effect = grpc.RpcError()
        mock_local.return_value = {
            'pattern': 'ATG',
            'total_matches': 1,
            'search_time_ms': 30.0,
            'matches': [],
            'algorithm_used': 'naive-local'
        }

        result = run_search("ATCGATCG", "ATG", allow_overlapping=True)

        mock_grpc.assert_called_once()
        mock_local.assert_called_once()
        self.assertEqual(result['algorithm_used'], 'naive-local')

    @override_settings(USE_GRPC_SEARCH=True)
    @patch('search_api.services.run_grpc_search')
    @patch('search_api.services.run_local_search')
    def test_fallback_on_generic_exception(self, mock_local, mock_grpc):
        """Debe hacer fallback en otras excepciones de gRPC"""
        mock_grpc.side_effect = Exception("Network error")
        # Este caso no debería hacer fallback según el código actual,
        # pero si se mejora para manejar más excepciones, este test aplica

        # El código actual solo maneja grpc.RpcError
        # Si se lanza otra excepción, se propagará
        with self.assertRaises(Exception):
            run_search("ATCGATCG", "ATG", allow_overlapping=True)


class EdgeCaseTests(TestCase):
    """Pruebas de casos límite"""

    def test_pattern_equals_sequence(self):
        """Patrón igual a secuencia debe encontrar 1 coincidencia"""
        result = run_local_search("ATCG", "ATCG", allow_overlapping=True)
        self.assertEqual(result['total_matches'], 1)

    def test_single_character_pattern(self):
        """Debe manejar patrones de un solo carácter"""
        result = run_local_search("ATCG", "A", allow_overlapping=True)
        self.assertEqual(result['total_matches'], 1)

    def test_repeating_pattern(self):
        """Debe manejar patrones repetitivos"""
        result = run_local_search("AAAA", "A", allow_overlapping=True)
        self.assertEqual(result['total_matches'], 4)

    def test_very_long_sequence(self):
        """Debe manejar secuencias muy largas"""
        long_seq = "ATCG" * 10000  # 40k bp
        result = run_local_search(long_seq, "ATG", allow_overlapping=True)
        self.assertGreater(result['total_matches'], 0)
        self.assertIsInstance(result['search_time_ms'], float)

    def test_pattern_with_n(self):
        """Debe manejar patrones con N"""
        result = run_local_search("ATCGNATCG", "CGN", allow_overlapping=True)
        self.assertEqual(result['total_matches'], 1)
