import grpc
from django.conf import settings

from .grpc_stubs import dna_search_pb2, dna_search_pb2_grpc


class GrpcSearchClient:
    """
    Cliente gRPC simple para el microservicio C++.
    """

    def __init__(self, host: str, port: str, timeout: float = 5.0):
        self.address = f"{host}:{port}"
        self.timeout = timeout
        opts = [
            ('grpc.max_send_message_length', 200 * 1024 * 1024),
            ('grpc.max_receive_message_length', 200 * 1024 * 1024),
        ]
        self.channel = grpc.insecure_channel(self.address, options=opts)
        self.stub = dna_search_pb2_grpc.DnaSearchStub(self.channel)

    def search(self, sequence: str, pattern: str, allow_overlapping: bool = True):
        req = dna_search_pb2.SearchRequest(
            sequence=sequence,
            pattern=pattern,
            allow_overlapping=allow_overlapping,
        )
        resp = self.stub.Search(req, timeout=self.timeout)
        return resp


def get_grpc_client():
    host = getattr(settings, "GRPC_HOST", "localhost")
    port = getattr(settings, "GRPC_PORT", "50051")
    timeout = float(getattr(settings, "GRPC_TIMEOUT_SECONDS", 5))
    return GrpcSearchClient(host, port, timeout)
