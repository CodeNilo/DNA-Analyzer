# DNA Search gRPC (C++)

Servicio gRPC que ejecuta búsqueda de patrones en secuencias de ADN usando KMP como base. Expone un RPC `Search` definido en `proto/dna_search.proto`.

## Requisitos
- CMake 3.15+
- Compilador C++17
- gRPC y Protobuf instalados (con `grpc_cpp_plugin` disponible)

## Estructura
```
proto/         # Contrato gRPC (.proto)
src/           # Código del servidor y algoritmos
build/         # Directorio de compilación (generado)
```

## Build
```bash
cmake -S . -B build
cmake --build build
```
El binario queda en `build/dna_search_server`.

## Ejecutar
```bash
./build/dna_search_server           # usa puerto 50051
# o con puerto custom:
GRPC_PORT=6000 ./build/dna_search_server
```

## Protocolo
Ver `proto/dna_search.proto`. RPC:
- Entrada: `SearchRequest { sequence, pattern, allow_overlapping }`
- Salida: `SearchResponse { matches { position, context_before, context_after }, total_matches, search_time_ms, algorithm_used }`

## Notas
- El algoritmo actual es KMP en C++ con soporte de solapamiento. Se puede extender con Boyer-Moore u otros.
- No incluye autenticación ni TLS; agregar según entorno.*** End Patch|()
