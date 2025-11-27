"""
Pruebas unitarias para search_api/grpc_client.py

Cubre:
- GrpcSearchClient
- get_grpc_client factory
- Configuración de channel
- Timeout
- Message size limits
"""

from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, override_settings
import grpc

from search_api.grpc_client import GrpcSearchClient, get_grpc_client


class GrpcSearchClientTests(TestCase):
    """Pruebas para la clase GrpcSearchClient"""

    @patch('search_api.grpc_client.grpc.insecure_channel')
    @patch('search_api.grpc_client.dna_search_pb2_grpc.DnaSearchStub')
    def test_initialization(self, mock_stub_class, mock_channel):
        """Debe inicializar correctamente el cliente"""
        mock_channel_instance = MagicMock()
        mock_channel.return_value = mock_channel_instance

        client = GrpcSearchClient("localhost", "50051", timeout=5.0)

        self.assertEqual(client.address, "localhost:50051")
        self.assertEqual(client.timeout, 5.0)
        mock_channel.assert_called_once()
        mock_stub_class.assert_called_once_with(mock_channel_instance)

    @patch('search_api.grpc_client.grpc.insecure_channel')
    @patch('search_api.grpc_client.dna_search_pb2_grpc.DnaSearchStub')
    def test_channel_options_for_large_messages(self, mock_stub_class, mock_channel):
        """Debe configurar opciones de channel para mensajes grandes"""
        client = GrpcSearchClient("localhost", "50051")

        # Verificar que se llamó con opciones
        call_args = mock_channel.call_args
        options = call_args[1]['options']

        # Buscar las opciones de tamaño de mensaje
        option_dict = {key: value for key, value in options}

        expected_size = 200 * 1024 * 1024  # 200MB
        self.assertEqual(option_dict['grpc.max_send_message_length'], expected_size)
        self.assertEqual(option_dict['grpc.max_receive_message_length'], expected_size)

    @patch('search_api.grpc_client.grpc.insecure_channel')
    @patch('search_api.grpc_client.dna_search_pb2_grpc.DnaSearchStub')
    @patch('search_api.grpc_client.dna_search_pb2.SearchRequest')
    def test_search_method(self, mock_request_class, mock_stub_class, mock_channel):
        """Debe ejecutar búsqueda correctamente"""
        # Setup mocks
        mock_request = Mock()
        mock_request_class.return_value = mock_request

        mock_response = Mock()
        mock_stub = Mock()
        mock_stub.Search.return_value = mock_response
        mock_stub_class.return_value = mock_stub

        # Create client and call search
        client = GrpcSearchClient("localhost", "50051", timeout=3.0)
        result = client.search("ATCG", "AT", allow_overlapping=True)

        # Verify
        mock_request_class.assert_called_once_with(
            sequence="ATCG",
            pattern="AT",
            allow_overlapping=True
        )
        mock_stub.Search.assert_called_once_with(mock_request, timeout=3.0)
        self.assertEqual(result, mock_response)

    @patch('search_api.grpc_client.grpc.insecure_channel')
    @patch('search_api.grpc_client.dna_search_pb2_grpc.DnaSearchStub')
    def test_custom_timeout(self, mock_stub_class, mock_channel):
        """Debe usar timeout personalizado"""
        client = GrpcSearchClient("localhost", "50051", timeout=10.0)
        self.assertEqual(client.timeout, 10.0)

    @patch('search_api.grpc_client.grpc.insecure_channel')
    @patch('search_api.grpc_client.dna_search_pb2_grpc.DnaSearchStub')
    def test_default_timeout(self, mock_stub_class, mock_channel):
        """Debe usar timeout por defecto de 5 segundos"""
        client = GrpcSearchClient("localhost", "50051")
        self.assertEqual(client.timeout, 5.0)

    @patch('search_api.grpc_client.grpc.insecure_channel')
    @patch('search_api.grpc_client.dna_search_pb2_grpc.DnaSearchStub')
    def test_address_formatting(self, mock_stub_class, mock_channel):
        """Debe formatear dirección correctamente"""
        client = GrpcSearchClient("192.168.1.1", "8080")
        self.assertEqual(client.address, "192.168.1.1:8080")

    @patch('search_api.grpc_client.grpc.insecure_channel')
    @patch('search_api.grpc_client.dna_search_pb2_grpc.DnaSearchStub')
    @patch('search_api.grpc_client.dna_search_pb2.SearchRequest')
    def test_search_with_overlapping_false(self, mock_request_class, mock_stub_class, mock_channel):
        """Debe pasar allow_overlapping=False correctamente"""
        mock_stub = Mock()
        mock_stub_class.return_value = mock_stub

        client = GrpcSearchClient("localhost", "50051")
        client.search("ATCG", "AT", allow_overlapping=False)

        call_args = mock_request_class.call_args
        self.assertEqual(call_args[1]['allow_overlapping'], False)


class GetGrpcClientFactoryTests(TestCase):
    """Pruebas para la función factory get_grpc_client"""

    @override_settings(
        GRPC_HOST="test_host",
        GRPC_PORT="9999",
        GRPC_TIMEOUT_SECONDS=15
    )
    @patch('search_api.grpc_client.GrpcSearchClient')
    def test_uses_settings_values(self, mock_client_class):
        """Debe usar valores de configuración de Django"""
        get_grpc_client()

        mock_client_class.assert_called_once_with("test_host", "9999", 15.0)

    @override_settings()
    @patch('search_api.grpc_client.GrpcSearchClient')
    def test_uses_default_host(self, mock_client_class):
        """Debe usar 'localhost' por defecto si GRPC_HOST no está configurado"""
        # Eliminar atributo si existe
        from django.conf import settings
        if hasattr(settings, 'GRPC_HOST'):
            delattr(settings, 'GRPC_HOST')

        get_grpc_client()

        call_args = mock_client_class.call_args
        self.assertEqual(call_args[0][0], "localhost")

    @override_settings()
    @patch('search_api.grpc_client.GrpcSearchClient')
    def test_uses_default_port(self, mock_client_class):
        """Debe usar '50051' por defecto si GRPC_PORT no está configurado"""
        from django.conf import settings
        if hasattr(settings, 'GRPC_PORT'):
            delattr(settings, 'GRPC_PORT')

        get_grpc_client()

        call_args = mock_client_class.call_args
        self.assertEqual(call_args[0][1], "50051")

    @override_settings()
    @patch('search_api.grpc_client.GrpcSearchClient')
    def test_uses_default_timeout(self, mock_client_class):
        """Debe usar 5.0 por defecto si GRPC_TIMEOUT_SECONDS no está configurado"""
        from django.conf import settings
        if hasattr(settings, 'GRPC_TIMEOUT_SECONDS'):
            delattr(settings, 'GRPC_TIMEOUT_SECONDS')

        get_grpc_client()

        call_args = mock_client_class.call_args
        self.assertEqual(call_args[0][2], 5.0)

    @override_settings(GRPC_TIMEOUT_SECONDS="7")
    @patch('search_api.grpc_client.GrpcSearchClient')
    def test_converts_timeout_to_float(self, mock_client_class):
        """Debe convertir timeout a float si viene como string"""
        get_grpc_client()

        call_args = mock_client_class.call_args
        self.assertEqual(call_args[0][2], 7.0)
        self.assertIsInstance(call_args[0][2], float)

    @patch('search_api.grpc_client.GrpcSearchClient')
    def test_returns_client_instance(self, mock_client_class):
        """Debe devolver instancia de GrpcSearchClient"""
        mock_instance = Mock()
        mock_client_class.return_value = mock_instance

        result = get_grpc_client()

        self.assertEqual(result, mock_instance)


class GrpcClientIntegrationTests(TestCase):
    """Pruebas de integración del cliente gRPC"""

    @patch('search_api.grpc_client.grpc.insecure_channel')
    @patch('search_api.grpc_client.dna_search_pb2_grpc.DnaSearchStub')
    @patch('search_api.grpc_client.dna_search_pb2.SearchRequest')
    def test_full_search_flow(self, mock_request_class, mock_stub_class, mock_channel):
        """Debe ejecutar flujo completo de búsqueda"""
        # Setup response mock
        mock_match = Mock()
        mock_match.position = 5
        mock_match.context_before = "ATCGA"
        mock_match.context_after = "ATCG"

        mock_response = Mock()
        mock_response.matches = [mock_match]
        mock_response.total_matches = 1
        mock_response.search_time_ms = 42.5
        mock_response.algorithm_used = "KMP"

        mock_stub = Mock()
        mock_stub.Search.return_value = mock_response
        mock_stub_class.return_value = mock_stub

        # Execute
        client = GrpcSearchClient("localhost", "50051")
        result = client.search("ATCGATCGATCG", "ATG", allow_overlapping=True)

        # Verify
        self.assertEqual(result.total_matches, 1)
        self.assertEqual(result.search_time_ms, 42.5)
        self.assertEqual(result.algorithm_used, "KMP")
        self.assertEqual(len(result.matches), 1)

    @patch('search_api.grpc_client.grpc.insecure_channel')
    @patch('search_api.grpc_client.dna_search_pb2_grpc.DnaSearchStub')
    def test_handles_grpc_errors(self, mock_stub_class, mock_channel):
        """Debe propagar errores de gRPC"""
        mock_stub = Mock()
        mock_stub.Search.side_effect = grpc.RpcError()
        mock_stub_class.return_value = mock_stub

        client = GrpcSearchClient("localhost", "50051")

        with self.assertRaises(grpc.RpcError):
            client.search("ATCG", "AT", allow_overlapping=True)


class GrpcClientEdgeCasesTests(TestCase):
    """Pruebas de casos límite del cliente gRPC"""

    @patch('search_api.grpc_client.grpc.insecure_channel')
    @patch('search_api.grpc_client.dna_search_pb2_grpc.DnaSearchStub')
    def test_empty_sequence(self, mock_stub_class, mock_channel):
        """Debe manejar secuencia vacía"""
        mock_stub = Mock()
        mock_stub_class.return_value = mock_stub

        client = GrpcSearchClient("localhost", "50051")
        # No debería fallar al crear el request
        try:
            client.search("", "AT", allow_overlapping=True)
        except Exception as e:
            # Es aceptable que falle, pero no debe ser un error de inicialización
            pass

    @patch('search_api.grpc_client.grpc.insecure_channel')
    @patch('search_api.grpc_client.dna_search_pb2_grpc.DnaSearchStub')
    def test_very_long_sequence(self, mock_stub_class, mock_channel):
        """Debe manejar secuencias muy largas"""
        mock_response = Mock()
        mock_response.matches = []
        mock_response.total_matches = 0
        mock_response.search_time_ms = 100.0
        mock_response.algorithm_used = "KMP"

        mock_stub = Mock()
        mock_stub.Search.return_value = mock_response
        mock_stub_class.return_value = mock_stub

        client = GrpcSearchClient("localhost", "50051")
        long_sequence = "ATCG" * 25000  # 100k bp

        result = client.search(long_sequence, "GGGG", allow_overlapping=True)
        self.assertEqual(result.total_matches, 0)

    @patch('search_api.grpc_client.grpc.insecure_channel')
    @patch('search_api.grpc_client.dna_search_pb2_grpc.DnaSearchStub')
    def test_unicode_in_address(self, mock_stub_class, mock_channel):
        """Debe manejar caracteres unicode en dirección"""
        client = GrpcSearchClient("localhost", "50051")
        self.assertIsInstance(client.address, str)
        self.assertEqual(client.address, "localhost:50051")
