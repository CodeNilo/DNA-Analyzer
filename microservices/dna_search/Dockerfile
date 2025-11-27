# Imagen base moderna con repositorios activos
FROM debian:bullseye-slim

WORKDIR /app

# Instala toolchain y gRPC/Protobuf (incluye grpc_cpp_plugin)
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libprotobuf-dev \
    protobuf-compiler \
    protobuf-compiler-grpc \
    libgrpc++-dev \
 && rm -rf /var/lib/apt/lists/*

# Copiamos el código del microservicio
COPY proto/ proto/
COPY src/ src/
COPY include/ include/
COPY CMakeLists.txt .

# Construimos el servidor
RUN cmake -S . -B build && cmake --build build

# Puerto gRPC (configurable)
ENV GRPC_PORT=50051
EXPOSE 50051

# Arranque del servidor
CMD ["./build/dna_search_server"]
