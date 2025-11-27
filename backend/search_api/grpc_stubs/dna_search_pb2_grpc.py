# Generated manually from proto/dna_search.proto for lightweight client use.
import grpc

from . import dna_search_pb2


class DnaSearchStub(object):
    def __init__(self, channel):
        self.Search = channel.unary_unary(
                '/dna.DnaSearch/Search',
                request_serializer=dna_search_pb2.SearchRequest.SerializeToString,
                response_deserializer=dna_search_pb2.SearchResponse.FromString,
                )


class DnaSearchServicer(object):
    def Search(self, request, context):
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_DnaSearchServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'Search': grpc.unary_unary_rpc_method_handler(
                    servicer.Search,
                    request_deserializer=dna_search_pb2.SearchRequest.FromString,
                    response_serializer=dna_search_pb2.SearchResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'dna.DnaSearch', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
