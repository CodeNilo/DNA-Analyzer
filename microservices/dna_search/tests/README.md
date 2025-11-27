# Pruebas Unitarias C++ - Algoritmo KMP

Este directorio contiene las pruebas unitarias para el algoritmo KMP implementado en C++.

## Requisitos

- CMake 3.15 o superior
- Google Test (gtest)
- Compilador C++17 compatible (g++, clang++)

## Instalación de Google Test

### Ubuntu/Debian
```bash
sudo apt-get install libgtest-dev
cd /usr/src/gtest
sudo cmake .
sudo make
sudo cp lib/*.a /usr/lib
```

### macOS (con Homebrew)
```bash
brew install googletest
```

### Windows (con vcpkg)
```bash
vcpkg install gtest
```

## Compilación y Ejecución

### Opción 1: Usando CMake directamente

```bash
# Desde el directorio tests/
mkdir build
cd build
cmake ..
make
./test_kmp
```

### Opción 2: Usando el target 'check'

```bash
cd build
make check
```

### Opción 3: Con verbose output

```bash
cd build
cmake ..
make
ctest --verbose
```

## Cobertura de Tests

Los tests cubren:

1. **Tabla LPS (Longest Proper Prefix Suffix)**
   - Patrones simples con repeticiones
   - Patrones sin repeticiones
   - Patrones mixtos
   - Casos extremos (vacío, un carácter)

2. **Búsqueda Básica**
   - Coincidencias simples
   - Sin coincidencias
   - Patrón al inicio/final
   - Patrón más largo que texto

3. **Búsqueda con Solapamiento**
   - Modo overlapping
   - Modo non-overlapping
   - Casos complejos

4. **Secuencias de ADN**
   - Codones de inicio (ATG)
   - Codones de terminación (TAA, TAG, TGA)
   - Secuencias con N

5. **Rendimiento y Casos Extremos**
   - Secuencias grandes (10k+ bp)
   - Patrones repetitivos
   - Textos vacíos
   - Patrones largos

6. **Corrección del Algoritmo**
   - Comparación con búsqueda naive
   - Múltiples patrones

## Estructura de Tests

```
tests/
├── CMakeLists.txt       # Configuración de CMake
├── test_kmp.cpp         # Pruebas unitarias
└── README.md            # Este archivo
```

## Ejecutar Tests Específicos

```bash
# Ejecutar solo tests que contienen "Overlapping" en el nombre
./test_kmp --gtest_filter="*Overlapping*"

# Ejecutar con output detallado
./test_kmp --gtest_verbose

# Listar todos los tests
./test_kmp --gtest_list_tests
```

## Integración Continua

Para integrar en CI/CD (GitHub Actions, Jenkins, etc.):

```yaml
- name: Build and run C++ tests
  run: |
    cd microservices/dna_search/tests
    mkdir build && cd build
    cmake ..
    make
    ./test_kmp
```

## Resultados Esperados

Todos los tests deben pasar (PASSED). Ejemplo de salida:

```
[==========] Running 30 tests from 1 test suite.
[----------] Global test environment set-up.
[----------] 30 tests from KMPTest
[ RUN      ] KMPTest.ComputeLPSSimplePattern
[       OK ] KMPTest.ComputeLPSSimplePattern (0 ms)
...
[----------] 30 tests from KMPTest (5 ms total)

[==========] 30 tests from 1 test suite ran. (5 ms total)
[  PASSED  ] 30 tests.
```

## Troubleshooting

### Error: gtest/gtest.h not found
Instala Google Test según las instrucciones de tu sistema operativo.

### Error: C++17 features not available
Actualiza tu compilador a una versión compatible con C++17.

### Tests fallan
Verifica que la implementación de KMP esté en `../src/algorithms/kmp.cpp` y el header en `../include/algorithms/kmp.h`.
