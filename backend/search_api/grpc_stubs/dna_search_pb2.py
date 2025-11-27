# Dynamically builds protobuf descriptors for dna_search.proto at import time.
from google.protobuf import descriptor_pb2, descriptor_pool, message_factory, symbol_database

_sym_db = symbol_database.Default()


def _build_file_descriptor():
    fdp = descriptor_pb2.FileDescriptorProto()
    fdp.name = "dna_search.proto"
    fdp.package = "dna"
    fdp.syntax = "proto3"

    # SearchRequest
    search_req = fdp.message_type.add()
    search_req.name = "SearchRequest"
    field = search_req.field.add()
    field.name = "sequence"
    field.number = 1
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
    field = search_req.field.add()
    field.name = "pattern"
    field.number = 2
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
    field = search_req.field.add()
    field.name = "allow_overlapping"
    field.number = 3
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_BOOL

    # Match
    match_msg = fdp.message_type.add()
    match_msg.name = "Match"
    field = match_msg.field.add()
    field.name = "position"
    field.number = 1
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_INT64
    field = match_msg.field.add()
    field.name = "context_before"
    field.number = 2
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING
    field = match_msg.field.add()
    field.name = "context_after"
    field.number = 3
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    # SearchResponse
    search_resp = fdp.message_type.add()
    search_resp.name = "SearchResponse"
    field = search_resp.field.add()
    field.name = "matches"
    field.number = 1
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_REPEATED
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_MESSAGE
    field.type_name = ".dna.Match"
    field = search_resp.field.add()
    field.name = "total_matches"
    field.number = 2
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_INT32
    field = search_resp.field.add()
    field.name = "search_time_ms"
    field.number = 3
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_DOUBLE
    field = search_resp.field.add()
    field.name = "algorithm_used"
    field.number = 4
    field.label = descriptor_pb2.FieldDescriptorProto.LABEL_OPTIONAL
    field.type = descriptor_pb2.FieldDescriptorProto.TYPE_STRING

    # Service DnaSearch with Search rpc
    service = fdp.service.add()
    service.name = "DnaSearch"
    method = service.method.add()
    method.name = "Search"
    method.input_type = ".dna.SearchRequest"
    method.output_type = ".dna.SearchResponse"

    serialized = fdp.SerializeToString()
    pool = descriptor_pool.Default()
    pool.AddSerializedFile(serialized)
    return pool.FindFileByName("dna_search.proto")


FILE_DESCRIPTOR = _build_file_descriptor()

SearchRequest = message_factory.GetMessageClass(FILE_DESCRIPTOR.message_types_by_name["SearchRequest"])
Match = message_factory.GetMessageClass(FILE_DESCRIPTOR.message_types_by_name["Match"])
SearchResponse = message_factory.GetMessageClass(FILE_DESCRIPTOR.message_types_by_name["SearchResponse"])

_sym_db.RegisterMessage(SearchRequest)
_sym_db.RegisterMessage(Match)
_sym_db.RegisterMessage(SearchResponse)
