# SISTEMA DE BÚSQUEDA DE SUBSECUENCIAS EN CADENAS DE ADN

## INFORMACIÓN GENERAL DEL PROYECTO

### Título
Sistema Web de Búsqueda de Subsecuencias en Cadenas de ADN mediante Arquitectura de Microservicios

### Descripción General
Aplicación web que permite a investigadores y profesionales del área de genética realizar búsquedas eficientes de subsecuencias (patrones) dentro de cadenas de ADN almacenadas en archivos CSV, utilizando algoritmos optimizados implementados en C++ y comunicados mediante gRPC con una aplicación Django.

### Contexto y Motivación
El análisis de secuencias de ADN es fundamental para la investigación genética moderna, medicina personalizada y biotecnología. Los investigadores necesitan constantemente buscar patrones específicos dentro de cadenas de ADN que pueden contener millones de nucleótidos. Las herramientas actuales enfrentan problemas de rendimiento y accesibilidad que este proyecto busca resolver.

---

## ARQUITECTURA DEL SISTEMA

### Stack Tecnológico

**Frontend y Backend Web:**
- Django (Python) - Framework web principal
- Django REST Framework - API REST interna
- HTML/CSS/JavaScript - Interfaz de usuario
- localStorage - Almacenamiento de historial en navegador

**Motor de Búsqueda:**
- C++ (C++11/14/17) - Implementación de algoritmos
- gRPC - Comunicación entre servicios
- Protocol Buffers - Definición de contratos

**Persistencia y Caché:**
- PostgreSQL - Base de datos principal
- Redis - Caché de resultados
- localStorage - Historial del usuario en navegador

**Procesamiento Asíncrono:**
- Celery - Cola de tareas para búsquedas largas
- Redis - Broker de mensajes para Celery

**Deployment:**
- Docker - Containerización (opcional v1.0)
- Nginx - Servidor web y proxy reverso
- Gunicorn - Servidor WSGI para Django

### Componentes Principales

```
┌─────────────────────────────────────────────────────────┐
│                    NAVEGADOR WEB                         │
│  ┌─────────────────┐        ┌──────────────────┐       │
│  │   Interfaz Web  │        │   localStorage    │       │
│  │   (HTML/CSS/JS) │        │  (Historial)      │       │
│  └────────┬────────┘        └──────────────────┘       │
└───────────┼──────────────────────────────────────────────┘
            │ HTTP/AJAX
┌───────────▼──────────────────────────────────────────────┐
│                  APLICACIÓN DJANGO                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │    Views     │  │   Services   │  │ Repositories │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                  │                  │          │
│  ┌──────▼──────────────────▼──────────────────▼───────┐ │
│  │              gRPC Client + Circuit Breaker         │ │
│  └──────────────────────────┬─────────────────────────┘ │
└─────────────────────────────┼───────────────────────────┘
                              │ gRPC
┌─────────────────────────────▼───────────────────────────┐
│              MICROSERVICIO C++ (gRPC Server)            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │     KMP      │  │ Boyer-Moore  │  │   Strategy   │ │
│  │  Algorithm   │  │  Algorithm   │  │   Selector   │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                    CAPA DE DATOS                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  PostgreSQL  │  │    Redis     │  │    Celery    │ │
│  │ (Secuencias) │  │   (Caché)    │  │   Workers    │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Patrones de Diseño Utilizados

**En Django:**
- **Layered Architecture** - Separación en capas (presentación, aplicación, dominio, infraestructura)
- **Repository Pattern** - Abstracción de acceso a datos
- **Service Layer Pattern** - Lógica de negocio encapsulada
- **Facade Pattern** - Simplificación de comunicación con microservicio
- **Strategy Pattern** - Selección de algoritmos de búsqueda
- **Circuit Breaker Pattern** - Resiliencia ante fallos del microservicio

**En Microservicio C++:**
- **Strategy Pattern** - Intercambio de algoritmos (KMP vs Boyer-Moore)
- **Single Responsibility Principle** - Separación de parsing, búsqueda y respuesta
- **RAII Pattern** - Gestión automática de recursos

---

## PLANTEAMIENTO DEL PROBLEMA

### Realidad Problemática

El análisis de secuencias de ADN es fundamental en la investigación genética moderna, la medicina personalizada y la biotecnología. Los científicos y laboratorios necesitan constantemente buscar patrones específicos dentro de cadenas de ADN que pueden contener millones o miles de millones de nucleótidos.

Actualmente, este proceso enfrenta varios problemas importantes:

1. **Problema de rendimiento:** Las herramientas tradicionales basadas en búsquedas simples son extremadamente lentas. Una búsqueda que podría tomar segundos con algoritmos optimizados puede tardar minutos u horas.

2. **Falta de especialización:** Las soluciones generales de análisis de texto no están optimizadas para ADN (solo 4 caracteres: A, T, C, G), desperdiciando oportunidades de optimización.

3. **Dificultad de acceso:** Muchas herramientas bioinformáticas requieren conocimientos técnicos avanzados, limitando su uso a especialistas.

4. **Procesamiento de volúmenes grandes:** Archivos CSV con secuencias pueden pesar gigabytes, y procesarlos eficientemente es complicado.

5. **Escalabilidad limitada:** Los sistemas actuales se degradan cuando múltiples investigadores trabajan simultáneamente.

Esta problemática genera retrasos en investigaciones críticas, aumenta costos operativos y limita la capacidad de descubrimiento científico.

### Justificación

#### Teórica

El proyecto permitirá implementar y validar algoritmos avanzados de búsqueda como KMP y Boyer-Moore en un contexto real de bioinformática, demostrando cómo la teoría se traduce en soluciones prácticas con impacto medible.

La arquitectura de microservicios valida el principio de separar componentes computacionalmente intensivos (C++) de la lógica de aplicación (Django), aprovechando las fortalezas de cada tecnología.

La integración mediante gRPC entre Python y C++ demuestra la viabilidad de combinar ecosistemas tecnológicos diferentes de manera robusta.

#### Metodológica

Este proyecto adopta un enfoque donde primero se diseña la arquitectura completa del sistema antes de comenzar a programar. Esta disciplina metodológica genera documentación valiosa que explica por qué el sistema está construido de cierta manera.

Se implementará un sistema de pruebas donde podamos medir el rendimiento de forma objetiva con datos reales, permitiendo saber exactamente en qué situaciones conviene usar cada algoritmo.

El proyecto desarrollará estrategias para manejar archivos CSV muy grandes mediante técnicas de streaming y procesamiento por lotes. Estos principios son útiles para cualquier aplicación que necesite procesar información masiva.

Desde el principio se incluirán herramientas para monitorear cómo funciona el sistema (logs, métricas, health checks), permitiendo detectar problemas temprano.

#### Práctica

Los investigadores podrán realizar búsquedas de patrones genéticos en segundos en lugar de minutos u horas, acelerando significativamente el ritmo de descubrimiento científico.

Al optimizar las búsquedas, se reducirá el consumo de recursos computacionales, disminuyendo costos de infraestructura.

Una interfaz web intuitiva permitirá que biólogos, médicos e investigadores sin formación en programación puedan realizar análisis complejos de ADN.

El sistema podrá atender múltiples usuarios simultáneos sin degradación de rendimiento.

La arquitectura desarrollada será adaptable a otros problemas de búsqueda de patrones en grandes volúmenes de datos.

---

## OBJETIVOS

### Objetivo General

Desarrollar un sistema web escalable basado en arquitectura de microservicios que permita a investigadores y profesionales del área de genética realizar búsquedas eficientes de subsecuencias dentro de cadenas de ADN almacenadas en archivos CSV, utilizando algoritmos optimizados implementados en C++ y comunicados mediante gRPC con una aplicación Django.

### Objetivos Específicos

1. **Diseñar la arquitectura del sistema:** Crear un diseño de microservicios que separe claramente las responsabilidades entre la interfaz web en Django y el motor de búsqueda en C++. Definir el contrato de comunicación mediante Protocol Buffers.

2. **Implementar el procesamiento de datos:** Desarrollar módulo de carga y validación de archivos CSV que soporte archivos grandes mediante streaming. Establecer sistema de persistencia eficiente.

3. **Desarrollar el motor de búsqueda:** Implementar en C++ al menos dos algoritmos (KMP y Boyer-Moore) optimizados para ADN. Construir servidor gRPC eficiente y concurrente.

4. **Crear la interfaz de usuario:** Desarrollar interfaz web intuitiva en Django que permita cargar archivos CSV y definir patrones de búsqueda sin conocimientos técnicos.

5. **Optimizar rendimiento y escalabilidad:** Optimizar comunicación entre Django y microservicio C++. Implementar caché para búsquedas repetidas.

6. **Garantizar resiliencia y confiabilidad:** Implementar patrones de resiliencia (Circuit Breaker, Retry, Timeout). Crear sistema de health checks y monitoreo.

7. **Validar el sistema:** Realizar pruebas de rendimiento comparativas entre algoritmos con datasets reales. Medir tiempos de respuesta bajo diferentes cargas.

---

## ANÁLISIS DEL PROBLEMA

### Identificación de Requerimientos

#### Requerimientos Funcionales

**RF1. Gestión de Secuencias de ADN**
- El sistema debe permitir cargar archivos CSV que contengan secuencias de ADN
- Debe validar que las secuencias contengan únicamente caracteres válidos (A, T, C, G, N)
- Debe almacenar metadatos de cada secuencia (nombre, longitud, fecha de carga)
- Debe permitir listar y consultar secuencias previamente cargadas

**RF2. Búsqueda de Patrones**
- El sistema debe permitir buscar una subsecuencia específica dentro de cadenas de ADN
- Debe soportar dos modos: coincidencia directa (sin solapamiento) y con solapamiento
- Debe retornar todas las posiciones donde se encuentre cada patrón
- Debe mostrar el contexto (nucleótidos adyacentes) de cada coincidencia

**RF3. Gestión de Trabajos de Búsqueda**
- Debe crear un registro de cada trabajo de búsqueda iniciado
- Debe mostrar el estado del trabajo (pendiente, en proceso, completado, fallido)
- Debe permitir consultar resultados de búsquedas anteriores
- Debe notificar al usuario cuando una búsqueda larga se complete

**RF4. Visualización de Resultados**
- Debe mostrar el número total de coincidencias encontradas
- Debe listar cada coincidencia con su posición exacta en la secuencia
- Debe generar estadísticas básicas (densidad de coincidencias, distribución)
- Debe permitir exportar resultados en formatos comunes (CSV, JSON)

**RF5. Gestión Local de Historial**
- El sistema debe almacenar el historial de búsquedas en localStorage del navegador
- Debe permitir consultar búsquedas anteriores mientras permanezcan en el cache local
- Debe permitir al usuario limpiar su historial local
- Debe mostrar advertencia de que el historial se perderá si limpia el cache
- Debe limitar el almacenamiento local a las últimas 50 búsquedas

#### Requerimientos No Funcionales

**RNF1. Rendimiento**
- Las búsquedas en secuencias de hasta 1 millón de nucleótidos deben completarse en <5 segundos
- El sistema debe soportar al menos 10 búsquedas concurrentes sin degradación significativa
- La carga de archivos CSV de hasta 100MB debe completarse en <1 minuto

**RNF2. Escalabilidad**
- La arquitectura debe permitir escalar horizontalmente el microservicio de búsqueda
- Debe soportar crecimiento en volumen de datos sin rediseño arquitectónico
- Debe manejar incrementos en carga de usuarios mediante load balancing

**RNF3. Disponibilidad**
- El sistema debe tener una disponibilidad objetivo del 99% durante horario laboral
- Debe implementar mecanismos de recuperación ante fallas del microservicio
- Debe mantener funcionalidad degradada si el microservicio está temporalmente no disponible

**RNF4. Usabilidad**
- La interfaz debe ser intuitiva para usuarios sin conocimientos de programación
- Los mensajes de error deben ser claros y orientados a la solución
- La documentación de usuario debe estar completa y accesible

**RNF5. Mantenibilidad**
- El código debe seguir principios SOLID y patrones de diseño establecidos
- Debe existir documentación técnica completa de la arquitectura
- Los componentes deben estar desacoplados para facilitar actualizaciones independientes

**RNF6. Seguridad**
- Toda comunicación con el microservicio debe estar encriptada (TLS)
- Los datos almacenados localmente deben manejarse según mejores prácticas
- Debe implementar rate limiting básico por IP para prevenir abuso

### Identificación de Funcionalidades

#### Coincidencia Directa

**Definición:**
Se refiere a los casos donde el patrón buscado aparece en la secuencia de ADN sin que las ocurrencias se solapen entre sí. Cada coincidencia es independiente y no comparte nucleótidos con las demás.

**Ejemplos:**
```
Secuencia: ATGATCATGATG
Patrón:    ATG
Resultado: Posiciones 0, 6, 9 (sin solapamiento)
```

**Manejo en el Sistema:**

Para casos de coincidencia directa, el sistema utiliza **Knuth-Morris-Pratt (KMP)** y **Boyer-Moore** en su forma estándar. Cuando se encuentra una coincidencia, el algoritmo avanza saltando toda la longitud del patrón.

**Algoritmos Utilizados:**

- **KMP:** Construye tabla de prefijos, no retrocede en la secuencia, O(n+m)
- **Boyer-Moore:** Usa reglas del mal carácter y buen sufijo, busca de derecha a izquierda en patrón, eficiente con alfabeto pequeño (ADN)

**Criterio de Selección:**
- KMP para patrones con muchas repeticiones internas
- Boyer-Moore para patrones sin muchas repeticiones

**Aplicaciones Biológicas:**
- Identificación de genes completos
- Localización de sitios de restricción enzimática
- Búsqueda de promotores o terminadores

#### Solapamiento

**Definición:**
Se refiere a los casos donde el patrón aparece de manera que las ocurrencias comparten nucleótidos entre sí.

**Ejemplos:**
```
Secuencia: AAAA
Patrón:    AAA
Resultado: Posiciones 0, 1 (comparten nucleótidos en posiciones 1 y 2)
```

**Manejo en el Sistema:**

El sistema modifica KMP y Boyer-Moore para que después de encontrar una coincidencia, avancen solo una posición en lugar de saltar toda la longitud del patrón.

**Aplicaciones Biológicas:**
- Detección de microsatélites (STRs)
- Identificación de expansiones de trinucleótidos (Huntington, X Frágil)
- Análisis de regiones de baja complejidad
- Detección de palíndromos

**Consideraciones:**
- En casos de alto solapamiento, el número de coincidencias puede ser muy elevado
- Sistema implementa límite de coincidencias máximas (100,000)
- Advertencias al usuario para patrones altamente repetitivos

### Definición de Alcances

#### Dentro del Alcance (Versión 1.0)

**Funcionalidades:**
- Carga de archivos CSV (hasta 100MB)
- Búsqueda de patrón único
- Soporte para coincidencia directa y solapamiento
- Algoritmos KMP y Boyer-Moore
- Comunicación Django-C++ vía gRPC
- Interfaz web intuitiva
- Visualización de resultados con posiciones y contexto
- Historial en localStorage (50 búsquedas)
- Exportación CSV/JSON
- Búsqueda síncrona (<1M nucleótidos) y asíncrona (>1M)
- Sistema de caché híbrido (localStorage + Redis)
- Validación multicapa

**Capacidades:**
- 10 usuarios concurrentes
- Deployment en servidor único
- Rate limiting: 100 búsquedas/hora por IP
- Logs estructurados
- Health checks básicos

**Límites:**
- Máximo 100MB por archivo
- Máximo 50 búsquedas en historial
- TTL de 7 días para resultados en servidor
- Máximo 100,000 coincidencias reportadas

#### Fuera del Alcance (Versión 1.0)

- Búsqueda de múltiples patrones (Aho-Corasick)
- Coincidencia aproximada
- Análisis estadístico avanzado
- Alineamiento de secuencias
- Visualización gráfica
- Formatos FASTA/FASTQ
- Integración NCBI/Ensembl
- Sistema de autenticación
- API pública
- Docker/Kubernetes

#### Roadmap

**v1.1 (3-4 meses):** Aho-Corasick, gráficos de densidad, FASTA export

**v1.2 (6 meses):** Autenticación opcional, API pública, compartir resultados

**v2.0 (12 meses):** Escalamiento, coincidencia aproximada, integración BLAST

### Identificación de Riesgos

#### Riesgos Técnicos

**RT1. Rendimiento en Casos de Alto Solapamiento**
- Probabilidad: Alta | Impacto: Alto
- Descripción: Patrones repetitivos pueden generar miles de coincidencias
- Mitigación: Límite de coincidencias, detección temprana, paginación, timeout

**RT2. Latencia en Comunicación gRPC**
- Probabilidad: Media | Impacto: Alto
- Descripción: Serialización puede agregar 100-500ms de latencia
- Mitigación: Benchmarks, connection pooling, compresión selectiva, caché

**RT3. Complejidad de Integración C++/Python**
- Probabilidad: Alta | Impacto: Medio
- Descripción: Diferencias en memoria y tipos pueden causar bugs
- Mitigación: Protocol Buffers, validación exhaustiva, suite de pruebas

**RT4. Gestión de Memoria en C++**
- Probabilidad: Media | Impacto: Alto
- Descripción: Memory leaks o uso excesivo degradan el microservicio
- Mitigación: Smart pointers, límites por request, profiling con Valgrind

**RT5. Desincronización de Contratos gRPC**
- Probabilidad: Media | Impacto: Medio
- Descripción: Cambios en .proto sin actualizar ambos lados
- Mitigación: Versionamiento estricto, tests de compatibilidad

**RT6. Rendimiento de Base de Datos**
- Probabilidad: Media | Impacto: Medio
- Descripción: Secuencias grandes degradan PostgreSQL
- Mitigación: Usar bytea, compresión, filesystem para >10MB

#### Riesgos de Rendimiento

**RP1. Parsing CSV Bloqueante**
- Probabilidad: Alta | Impacto: Medio
- Descripción: Archivos grandes bloquean workers
- Mitigación: Streaming, Celery para >10MB, progreso visual

**RP2. Saturación del Microservicio**
- Probabilidad: Media | Impacto: Alto
- Descripción: Búsquedas simultáneas agotan recursos
- Mitigación: Queue limitado, Circuit Breaker, rate limiting, monitoreo

**RP3. Implementación Incorrecta de Algoritmos**
- Probabilidad: Baja | Impacto: Alto
- Descripción: Algoritmos mal implementados no ofrecen ventajas
- Mitigación: Suite de pruebas, benchmarking, profiling, code review

#### Riesgos de Proyecto

**RPj1. Subestimación de Complejidad**
- Probabilidad: Alta | Impacto: Alto
- Descripción: Integración heterogénea toma más tiempo
- Mitigación: Prototipos tempranos, iteraciones, buffer 30%

**RPj2. Falta de Expertise en C++**
- Probabilidad: Media | Impacto: Medio
- Descripción: Curva de aprendizaje en C++ moderno
- Mitigación: Capacitación previa, code reviews, pair programming

**RPj3. Scope Creep**
- Probabilidad: Alta | Impacto: Medio
- Descripción: Agregar funcionalidades no planificadas
- Mitigación: Alcance documentado, proceso formal, backlog visible

**RPj4. Integración Tardía**
- Probabilidad: Media | Impacto: Alto
- Descripción: Incompatibilidades al juntar componentes
- Mitigación: Integración continua, tests diarios, desarrollo iterativo

#### Riesgos Operacionales

**RO1. Falta de Monitoreo**
- Probabilidad: Media | Impacto: Alto
- Descripción: Problemas pasan desapercibidos
- Mitigación: Logging desde inicio, métricas críticas, alertas

**RO2. Complejidad de Deployment**
- Probabilidad: Media | Impacto: Medio
- Descripción: Coordinar deployment de múltiples componentes
- Mitigación: Docker, scripts automatizados, staging idéntico

**RO3. Falta de Backups**
- Probabilidad: Baja | Impacto: Alto
- Descripción: Pérdida de datos sin backup
- Mitigación: Backups diarios, retención 30 días, testing de restauración

**RO4. Falta de Documentación**
- Probabilidad: Alta | Impacto: Medio
- Descripción: Mantenimiento futuro difícil
- Mitigación: README completo, arquitectura documentada, runbook

---

## ESPECIFICACIONES TÉCNICAS DETALLADAS

### Contrato gRPC (Protocol Buffers)

```protobuf
syntax = "proto3";

package dna_search;

service DNASearchService {
  rpc SearchPattern(SearchRequest) returns (SearchResponse);
  rpc HealthCheck(HealthRequest) returns (HealthResponse);
}

message SearchRequest {
  string sequence_id = 1;
  string dna_sequence = 2;
  string pattern = 3;
  bool allow_overlapping = 4;
  int32 max_matches = 5;
}

message SearchResponse {
  repeated Match matches = 1;
  int32 total_matches = 2;
  double search_time_ms = 3;
  string algorithm_used = 4;
  bool truncated = 5;
}

message Match {
  int64 position = 1;
  string context_before = 2;
  string context_after = 3;
}

message HealthRequest {}

message HealthResponse {
  bool healthy = 1;
  string status = 2;
}
```

### Modelos Django

```python
# models.py

from django.db import models
from django.utils import timezone

class DNASequence(models.Model):
    name = models.CharField(max_length=255)
    sequence = models.TextField()  # o BinaryField con compresión
    length = models.IntegerField()
    uploaded_at = models.DateTimeField(default=timezone.now)
    file_hash = models.CharField(max_length=64, unique=True)
    
    class Meta:
        db_table = 'dna_sequences'
        indexes = [
            models.Index(fields=['uploaded_at']),
            models.Index(fields=['file_hash']),
        ]

class SearchJob(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('PROCESSING', 'En Proceso'),
        ('COMPLETED', 'Completado'),
        ('FAILED', 'Fallido'),
    ]
    
    sequence = models.ForeignKey(DNASequence, on_delete=models.CASCADE)
    pattern = models.CharField(max_length=1000)
    allow_overlapping = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    total_matches = models.IntegerField(null=True)
    search_time_ms = models.FloatField(null=True)
    algorithm_used = models.CharField(max_length=50, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True)
    error_message = models.TextField(null=True)
    
    class Meta:
        db_table = 'search_jobs'
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]

class SearchResult(models.Model):
    job = models.ForeignKey(SearchJob, on_delete=models.CASCADE, related_name='results')
    position = models.BigIntegerField()
    context_before = models.CharField(max_length=50)
    context_after = models.CharField(max_length=50)
    
    class Meta:
        db_table = 'search_results'
        indexes = [
            models.Index(fields=['job', 'position']),
        ]
```

### Estructura del Proyecto

```
proyecto-adn/
├── backend/
│   ├── dna_search/              # Aplicación Django principal
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   ├── sequences/               # App de gestión de secuencias
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── services.py
│   │   ├── repositories.py
│   │   ├── validators.py
│   │   └── urls.py
│   ├── search/                  # App de búsqueda
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── services.py
│   │   ├── grpc_client.py
│   │   ├── tasks.py            # Celery tasks
│   │   └── urls.py
│   ├── grpc_protos/            # Protocol Buffers
│   │   ├── dna_search.proto
│   │   └── generated/          # Código generado
│   ├── static/
│   ├── templates/
│   ├── manage.py
│   └── requirements.txt
│
├── microservice/               # Microservicio C++
│   ├── src/
│   │   ├── main.cpp
│   │   ├── algorithms/
│   │   │   ├── kmp.h
│   │   │   ├── kmp.cpp
│   │   │   ├── boyer_moore.h
│   │   │   ├── boyer_moore.cpp
│   │   │   └── strategy.h
│   │   ├── grpc/
│   │   │   ├── server.h
│   │   │   ├── server.cpp
│   │   │   └── service_impl.cpp
│   │   └── utils/
│   │       ├── validator.h
│   │       └── validator.cpp
│   ├── protos/
│   │   └── dna_search.proto
│   ├── CMakeLists.txt
│   └── README.md
│
├── docker/
│   ├── Dockerfile.django
│   ├── Dockerfile.microservice
│   └── docker-compose.yml
│
├── docs/
│   ├── arquitectura.md
│   ├── api.md
│   ├── guia-usuario.md
│   └── deployment.md
│
└── README.md
```

### Algoritmos - Pseudocódigo

#### Knuth-Morris-Pratt (KMP)

**Sin Solapamiento:**
```
función KMP_SinSolape(texto, patrón):
    n = longitud(texto)
    m = longitud(patrón)
    lps = construirTablaLPS(patrón)
    coincidencias = []
    
    i = 0  // índice para texto
    j = 0  // índice para patrón
    
    mientras i < n:
        si texto[i] == patrón[j]:
            i++
            j++
        
        si j == m:
            // Encontró coincidencia
            coincidencias.agregar(i - j)
            j = 0  // Reiniciar para evitar solapamiento
            // i ya está en la posición correcta
        sino si i < n y texto[i] != patrón[j]:
            si j != 0:
                j = lps[j - 1]
            sino:
                i++
    
    retornar coincidencias

función construirTablaLPS(patrón):
    m = longitud(patrón)
    lps = arreglo[m]
    lps[0] = 0
    longitud = 0
    i = 1
    
    mientras i < m:
        si patrón[i] == patrón[longitud]:
            longitud++
            lps[i] = longitud
            i++
        sino:
            si longitud != 0:
                longitud = lps[longitud - 1]
            sino:
                lps[i] = 0
                i++
    
    retornar lps
```

**Con Solapamiento:**
```
función KMP_ConSolape(texto, patrón):
    n = longitud(texto)
    m = longitud(patrón)
    lps = construirTablaLPS(patrón)
    coincidencias = []
    
    i = 0
    j = 0
    
    mientras i < n:
        si texto[i] == patrón[j]:
            i++
            j++
        
        si j == m:
            // Encontró coincidencia
            coincidencias.agregar(i - j)
            j = lps[j - 1]  // Usar LPS para permitir solapamiento
        sino si i < n y texto[i] != patrón[j]:
            si j != 0:
                j = lps[j - 1]
            sino:
                i++
    
    retornar coincidencias
```

#### Boyer-Moore

**Construcción de Tabla de Mal Carácter:**
```
función construirTablaMalCaracter(patrón):
    m = longitud(patrón)
    tabla = mapa_vacío()
    
    // Por defecto, todos los caracteres tienen desplazamiento m
    para cada carácter c en alfabeto:
        tabla[c] = m
    
    // Actualizar con posiciones reales del patrón
    para i = 0 hasta m - 2:
        tabla[patrón[i]] = m - 1 - i
    
    retornar tabla
```

**Sin Solapamiento:**
```
función BoyerMoore_SinSolape(texto, patrón):
    n = longitud(texto)
    m = longitud(patrón)
    tablaMC = construirTablaMalCaracter(patrón)
    coincidencias = []
    
    s = 0  // desplazamiento del patrón respecto al texto
    
    mientras s <= n - m:
        j = m - 1
        
        // Comparar de derecha a izquierda
        mientras j >= 0 y patrón[j] == texto[s + j]:
            j--
        
        si j < 0:
            // Encontró coincidencia
            coincidencias.agregar(s)
            s += m  // Saltar longitud completa del patrón
        sino:
            // Usar regla del mal carácter
            s += max(1, tablaMC[texto[s + j]])
    
    retornar coincidencias
```

**Con Solapamiento:**
```
función BoyerMoore_ConSolape(texto, patrón):
    n = longitud(texto)
    m = longitud(patrón)
    tablaMC = construirTablaMalCaracter(patrón)
    coincidencias = []
    
    s = 0
    
    mientras s <= n - m:
        j = m - 1
        
        mientras j >= 0 y patrón[j] == texto[s + j]:
            j--
        
        si j < 0:
            // Encontró coincidencia
            coincidencias.agregar(s)
            s += 1  // Avanzar solo una posición
        sino:
            s += max(1, tablaMC[texto[s + j]])
    
    retornar coincidencias
```

### Flujos de Trabajo Principales

#### Flujo 1: Carga de Archivo CSV

```
1. Usuario selecciona archivo CSV desde interfaz
2. Frontend valida:
   - Extensión .csv
   - Tamaño < 100MB
   - Formato básico
3. Si válido, inicia carga con AJAX
4. Django recibe archivo
5. Si archivo > 10MB:
   - Crear tarea Celery asíncrona
   - Retornar job_id al usuario
   - Mostrar barra de progreso
6. Si archivo < 10MB:
   - Procesar síncronamente
7. Procesamiento:
   - Leer CSV línea por línea (streaming)
   - Validar cada secuencia (solo A,T,C,G,N)
   - Calcular hash del archivo
   - Verificar si ya existe (evitar duplicados)
   - Si no existe, guardar en PostgreSQL
8. Retornar resultado:
   - ID de la secuencia
   - Nombre
   - Longitud
   - Metadatos
9. Frontend muestra confirmación
```

#### Flujo 2: Búsqueda de Patrón (Síncrona)

```
1. Usuario ingresa:
   - Patrón a buscar
   - Selecciona secuencia (de lista)
   - Modo: permitir solapamiento (sí/no)
2. Frontend valida:
   - Patrón no vacío
   - Solo caracteres válidos
   - Longitud razonable
3. Django recibe request
4. Determinar si búsqueda es síncrona o asíncrona:
   - Si secuencia < 1M nucleótidos: SÍNCRONA
   - Si secuencia > 1M nucleótidos: ASÍNCRONA (ver Flujo 3)
5. Para búsqueda síncrona:
   - Verificar caché Redis:
     - Key: hash(secuencia_id + patrón + modo_solapamiento)
     - Si existe: retornar resultados cacheados
   - Si no hay caché:
     - Preparar SearchRequest gRPC
     - Llamar a microservicio C++ con timeout 30s
     - Microservicio ejecuta algoritmo apropiado
     - Retorna SearchResponse
6. Guardar en SearchJob y SearchResult (PostgreSQL)
7. Cachear en Redis (TTL 24h)
8. Retornar a frontend:
   - Total de coincidencias
   - Lista de posiciones
   - Contexto de cada coincidencia
   - Tiempo de búsqueda
   - Algoritmo usado
9. Frontend renderiza resultados
10. Guardar en localStorage del navegador:
    - Metadatos de búsqueda
    - Primeras 100 coincidencias
    - Timestamp
```

#### Flujo 3: Búsqueda de Patrón (Asíncrona)

```
1. Usuario inicia búsqueda (mismo input que Flujo 2)
2. Django determina: secuencia > 1M nucleótidos
3. Crear SearchJob con status=PENDING
4. Crear tarea Celery asíncrona
5. Retornar job_id al usuario inmediatamente
6. Frontend inicia polling cada 2 segundos:
   - GET /api/search/jobs/{job_id}/status
7. Worker Celery ejecuta:
   - Actualizar status=PROCESSING
   - Llamar microservicio C++ vía gRPC
   - Esperar respuesta (puede tomar minutos)
   - Guardar resultados
   - Actualizar status=COMPLETED
8. Frontend detecta completado en polling
9. Obtener resultados completos:
   - GET /api/search/jobs/{job_id}/results
10. Renderizar resultados
11. Guardar en localStorage (solo metadatos si muy grande)
```

#### Flujo 4: Consulta de Historial

```
1. Usuario abre sección "Historial"
2. Frontend lee localStorage:
   - Obtener array de búsquedas pasadas
   - Ordenar por fecha (más reciente primero)
3. Renderizar lista:
   - Fecha y hora
   - Patrón buscado
   - Nombre de secuencia
   - Total de coincidencias
   - Link para ver detalles
4. Usuario hace clic en búsqueda anterior
5. Si resultados están en localStorage:
   - Cargar y mostrar inmediatamente
6. Si resultados solo tienen referencia (búsqueda pesada):
   - Obtener de servidor: GET /api/search/jobs/{job_id}/results
   - Mostrar resultados
7. Opción de exportar:
   - CSV: generar y descargar
   - JSON: generar y descargar
```

### Estructura de localStorage

```javascript
// Estructura de datos en localStorage

// Key: 'dna_search_history'
{
  "version": "1.0",
  "searches": [
    {
      "id": "local_1699123456789",
      "timestamp": "2024-11-16T10:30:00Z",
      "pattern": "ATCG",
      "sequenceName": "genome_chr1.csv",
      "sequenceId": "seq_12345",
      "allowOverlapping": true,
      "totalMatches": 42,
      "searchTimeMs": 123.45,
      "algorithmUsed": "KMP",
      "resultsStored": "local", // o "server" si muy grande
      "results": [
        {
          "position": 0,
          "contextBefore": "-----",
          "contextAfter": "TACG"
        },
        // ... hasta 100 resultados
      ],
      "serverJobId": null // o job_id si está en servidor
    }
    // ... hasta 50 búsquedas
  ],
  "maxSize": 50
}

// Funciones de gestión
function addToHistory(searchData) {
  let history = JSON.parse(localStorage.getItem('dna_search_history') || '{"version":"1.0","searches":[],"maxSize":50}');
  
  // Agregar al inicio
  history.searches.unshift(searchData);
  
  // Mantener solo últimas 50
  if (history.searches.length > history.maxSize) {
    history.searches = history.searches.slice(0, history.maxSize);
  }
  
  localStorage.setItem('dna_search_history', JSON.stringify(history));
}

function getHistory() {
  let history = JSON.parse(localStorage.getItem('dna_search_history') || '{"version":"1.0","searches":[],"maxSize":50}');
  return history.searches;
}

function clearHistory() {
  localStorage.removeItem('dna_search_history');
}

function exportHistory() {
  let history = JSON.parse(localStorage.getItem('dna_search_history') || '{"version":"1.0","searches":[]}');
  let blob = new Blob([JSON.stringify(history, null, 2)], {type: 'application/json'});
  let url = URL.createObjectURL(blob);
  let a = document.createElement('a');
  a.href = url;
  a.download = 'dna_search_history.json';
  a.click();
}

function importHistory(file) {
  let reader = new FileReader();
  reader.onload = function(e) {
    try {
      let imported = JSON.parse(e.target.result);
      if (imported.version && imported.searches) {
        localStorage.setItem('dna_search_history', JSON.stringify(imported));
        alert('Historial importado correctamente');
      } else {
        alert('Formato de archivo inválido');
      }
    } catch(error) {
      alert('Error al importar: ' + error.message);
    }
  };
  reader.readAsText(file);
}
```

### Configuración de Django

```python
# settings.py

# gRPC Microservice
GRPC_MICROSERVICE_HOST = os.getenv('GRPC_HOST', 'localhost')
GRPC_MICROSERVICE_PORT = os.getenv('GRPC_PORT', '50051')
GRPC_MAX_WORKERS = 10
GRPC_TIMEOUT_SECONDS = 30

# Celery
CELERY_BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutos máximo

# Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://localhost:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'dna_search',
        'TIMEOUT': 86400,  # 24 horas
    }
}

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'dna_search'),
        'USER': os.getenv('DB_USER', 'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}

# File Upload
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100 MB

# Rate Limiting
RATELIMIT_ENABLE = True
RATELIMIT_USE_CACHE = 'default'
```

### Ejemplos de Uso de API

```python
# Cliente Python de ejemplo

import requests

BASE_URL = "http://localhost:8000/api"

# 1. Cargar secuencia
def upload_sequence(csv_file_path):
    with open(csv_file_path, 'rb') as f:
        files = {'file': f}
        response = requests.post(f"{BASE_URL}/sequences/upload/", files=files)
        return response.json()

# 2. Listar secuencias
def list_sequences():
    response = requests.get(f"{BASE_URL}/sequences/")
    return response.json()

# 3. Buscar patrón (síncrono)
def search_pattern(sequence_id, pattern, allow_overlapping=True):
    data = {
        'sequence_id': sequence_id,
        'pattern': pattern,
        'allow_overlapping': allow_overlapping
    }
    response = requests.post(f"{BASE_URL}/search/", json=data)
    return response.json()

# 4. Buscar patrón (asíncrono)
def search_pattern_async(sequence_id, pattern, allow_overlapping=True):
    data = {
        'sequence_id': sequence_id,
        'pattern': pattern,
        'allow_overlapping': allow_overlapping,
        'async': True
    }
    response = requests.post(f"{BASE_URL}/search/", json=data)
    return response.json()  # retorna {'job_id': '...'}

# 5. Consultar estado de trabajo
def get_job_status(job_id):
    response = requests.get(f"{BASE_URL}/search/jobs/{job_id}/status/")
    return response.json()

# 6. Obtener resultados
def get_search_results(job_id, page=1, page_size=100):
    response = requests.get(
        f"{BASE_URL}/search/jobs/{job_id}/results/",
        params={'page': page, 'page_size': page_size}
    )
    return response.json()

# 7. Exportar resultados
def export_results(job_id, format='csv'):
    response = requests.get(
        f"{BASE_URL}/search/jobs/{job_id}/export/",
        params={'format': format}
    )
    return response.content

# Ejemplo de uso completo
if __name__ == "__main__":
    # Cargar secuencia
    seq = upload_sequence("mi_genoma.csv")
    print(f"Secuencia cargada: {seq['id']}")
    
    # Buscar patrón
    result = search_pattern(seq['id'], "ATCG", allow_overlapping=True)
    print(f"Encontradas {result['total_matches']} coincidencias")
    
    # Si es búsqueda grande, usar asíncrono
    job = search_pattern_async(seq['id'], "AAAA", allow_overlapping=True)
    job_id = job['job_id']
    
    # Polling hasta completar
    import time
    while True:
        status = get_job_status(job_id)
        print(f"Estado: {status['status']}")
        if status['status'] in ['COMPLETED', 'FAILED']:
            break
        time.sleep(2)
    
    # Obtener resultados
    if status['status'] == 'COMPLETED':
        results = get_search_results(job_id)
        print(f"Total: {results['total_matches']}")
        print(f"Resultados página 1: {len(results['results'])}")
```

---

## GUÍA DE IMPLEMENTACIÓN

### Fase 1: Setup Inicial (Semana 1)

**Objetivo:** Preparar entorno de desarrollo y estructura base

**Tareas:**
1. Configurar repositorio Git
2. Crear estructura de carpetas del proyecto
3. Instalar dependencias:
   - Python 3.9+, Django 4.2+
   - C++ compiler (g++ o clang)
   - gRPC y Protocol Buffers
   - PostgreSQL
   - Redis
4. Configurar entornos virtuales
5. Crear proyecto Django base
6. Configurar base de datos PostgreSQL
7. Crear archivo .proto con contrato inicial
8. Documentar proceso de setup en README

**Entregables:**
- Repositorio configurado
- Django corriendo en localhost
- Base de datos conectada
- Archivo .proto compilando correctamente

### Fase 2: Microservicio C++ Básico (Semana 2-3)

**Objetivo:** Implementar microservicio con búsqueda básica

**Tareas:**
1. Implementar algoritmo KMP básico en C++
2. Implementar algoritmo Boyer-Moore básico
3. Crear servidor gRPC en C++
4. Implementar servicio SearchPattern
5. Agregar validación de input
6. Implementar health check
7. Crear tests unitarios para algoritmos
8. Documentar compilación y ejecución

**Entregables:**
- Microservicio compilando y corriendo
- Algoritmos probados y funcionando
- Tests pasando
- Documentación de API

### Fase 3: Integración Django-gRPC (Semana 4)

**Objetivo:** Conectar Django con microservicio

**Tareas:**
1. Generar código Python desde .proto
2. Crear cliente gRPC en Django
3. Implementar connection pooling
4. Agregar manejo de errores
5. Implementar Circuit Breaker básico
6. Crear endpoint de prueba
7. Tests de integración
8. Logging de comunicación gRPC

**Entregables:**
- Django puede llamar a microservicio
- Manejo robusto de errores
- Tests de integración pasando

### Fase 4: Carga de Archivos CSV (Semana 5)

**Objetivo:** Implementar carga y validación de secuencias

**Tareas:**
1. Crear modelos Django (DNASequence)
2. Implementar vista de carga
3. Validación de archivos CSV
4. Streaming para archivos grandes
5. Cálculo de hash para evitar duplicados
6. Almacenamiento en PostgreSQL
7. API endpoint para listar secuencias
8. Tests de carga

**Entregables:**
- Carga de CSV funcionando
- Validación robusta
- API de secuencias completa

### Fase 5: Búsqueda Completa (Semana 6-7)

**Objetivo:** Implementar flujo completo de búsqueda

**Tareas:**
1. Crear modelos SearchJob y SearchResult
2. Implementar servicio de búsqueda en Django
3. Integrar con microservicio C++
4. Implementar modo síncrono
5. Implementar modo asíncrono con Celery
6. Sistema de caché con Redis
7. Paginación de resultados
8. Exportación CSV/JSON
9. Tests end-to-end

**Entregables:**
- Búsqueda síncrona funcionando
- Búsqueda asíncrona funcionando
- Cache operativo
- Exportación funcionando

### Fase 6: Soporte para Solapamiento (Semana 8)

**Objetivo:** Implementar ambos modos de búsqueda

**Tareas:**
1. Modificar algoritmos C++ para soportar solapamiento
2. Agregar parámetro allow_overlapping en .proto
3. Actualizar cliente gRPC
4. Implementar selección de modo en API
5. Tests comparativos entre modos
6. Optimización para casos de alto solapamiento
7. Límites y advertencias

**Entregables:**
- Ambos modos funcionando correctamente
- Tests validando diferencias
- Límites implementados

### Fase 7: Interfaz de Usuario (Semana 9-10)

**Objetivo:** Crear interfaz web completa

**Tareas:**
1. Diseñar wireframes de interfaz
2. Implementar página de carga de archivos
3. Implementar formulario de búsqueda
4. Visualización de resultados
5. Integración con localStorage
6. Página de historial
7. Exportación/Importación de historial
8. Responsive design
9. Manejo de errores en UI

**Entregables:**
- Interfaz completa y funcional
- localStorage integrado
- Experiencia de usuario fluida

### Fase 8: Monitoreo y Resiliencia (Semana 11)

**Objetivo:** Implementar observabilidad y manejo de errores

**Tareas:**
1. Configurar logging estructurado
2. Implementar métricas básicas
3. Health checks completos
4. Circuit Breaker robusto
5. Timeouts configurables
6. Retry logic
7. Dashboard de monitoreo simple
8. Alertas básicas

**Entregables:**
- Sistema de logging operativo
- Métricas siendo recolectadas
- Resiliencia probada

### Fase 9: Testing y Optimización (Semana 12)

**Objetivo:** Asegurar calidad y rendimiento

**Tareas:**
1. Suite completa de tests unitarios
2. Tests de integración
3. Tests de carga con JMeter/Locust
4. Profiling de rendimiento
5. Optimización de queries SQL
6. Optimización de algoritmos C++
7. Benchmarking de ambos modos
8. Documentación de resultados

**Entregables:**
- Cobertura de tests >80%
- Benchmarks documentados
- Optimizaciones implementadas

### Fase 10: Documentación y Deployment (Semana 13)

**Objetivo:** Preparar para producción

**Tareas:**
1. Documentación de arquitectura completa
2. Guía de usuario con ejemplos
3. Documentación de API
4. Runbook operacional
5. Scripts de deployment
6. Configuración de producción
7. Plan de backup
8. Plan de rollback

**Entregables:**
- Documentación completa
- Scripts de deployment probados
- Sistema listo para producción

---

## CASOS DE PRUEBA IMPORTANTES

### Tests de Algoritmos

```
Test 1: Patrón no existe
- Secuencia: ATCGATCG
- Patrón: GGG
- Esperado: 0 coincidencias

Test 2: Patrón existe una vez
- Secuencia: ATCGATCG
- Patrón: TCGA
- Esperado: 1 coincidencia en posición 1

Test 3: Patrón existe múltiples veces sin solapamiento
- Secuencia: ATGATGATG
- Patrón: ATG
- Modo: Sin solapamiento
- Esperado: 3 coincidencias en posiciones 0, 3, 6

Test 4: Patrón con solapamiento
- Secuencia: AAAA
- Patrón: AAA
- Modo: Con solapamiento
- Esperado: 2 coincidencias en posiciones 0, 1

Test 5: Patrón idéntico a secuencia
- Secuencia: ATCG
- Patrón: ATCG
- Esperado: 1 coincidencia en posición 0

Test 6: Patrón más largo que secuencia
- Secuencia: ATC
- Patrón: ATCGATCG
- Esperado: 0 coincidencias

Test 7: Secuencia vacía
- Secuencia: ""
- Patrón: ATG
- Esperado: Error o 0 coincidencias

Test 8: Patrón vacío
- Secuencia: ATCG
- Patrón: ""
- Esperado: Error

Test 9: Alto solapamiento (caso extremo)
- Secuencia: AAAAAAAAAA (10 A's)
- Patrón: AAA
- Modo: Con solapamiento
- Esperado: 8 coincidencias

Test 10: Comparación KMP vs Boyer-Moore
- Secuencia: [genoma real de 1M nucleótidos]
- Patrón: ATCGATCG
- Verificar: Ambos retornan mismos resultados
```

### Tests de Integración

```
Test 11: Carga de archivo válido
- Archivo: secuencia_valida.csv
- Esperado: Secuencia guardada, retorna ID

Test 12: Carga de archivo inválido (caracteres incorrectos)
- Archivo: secuencia_invalida.csv (contiene X, Y)
- Esperado: Error 400 con mensaje claro

Test 13: Carga de archivo muy grande
- Archivo: genoma_100mb.csv
- Esperado: Procesamiento asíncrono, retorna job_id

Test 14: Búsqueda síncrona completa
- Cargar secuencia → Buscar patrón → Verificar resultados
- Esperado: Resultados correctos en <5 segundos

Test 15: Búsqueda asíncrona completa
- Cargar secuencia grande → Buscar patrón → Poll status → Obtener resultados
- Esperado: Status transitions correctos, resultados válidos

Test 16: Cache funciona
- Búsqueda 1: ejecuta y cachea
- Búsqueda 2: mismo patrón y secuencia
- Esperado: Búsqueda 2 retorna instantáneamente desde cache

Test 17: Circuit Breaker activa
- Detener microservicio C++
- Intentar búsqueda
- Esperado: Error manejado gracefully, Circuit Breaker abre
```

### Tests de Rendimiento

```
Test 18: Throughput con 10 usuarios concurrentes
- 10 usuarios buscan diferentes patrones simultáneamente
- Esperado: Todas completan en tiempo razonable

Test 19: Latencia de comunicación gRPC
- Medir tiempo de roundtrip Django → gRPC → Django
- Esperado: <100ms para búsquedas simples

Test 20: Consumo de memoria
- Búsqueda en secuencia de 100MB
- Esperado: Memoria del microservicio <1GB
```

---

## RECURSOS Y REFERENCIAS

### Documentación Oficial

- **Django:** https://docs.djangoproject.com/
- **Django REST Framework:** https://www.django-rest-framework.org/
- **gRPC:** https://grpc.io/docs/
- **Protocol Buffers:** https://protobuf.dev/
- **Celery:** https://docs.celeryproject.org/
- **PostgreSQL:** https://www.postgresql.org/docs/
- **Redis:** https://redis.io/documentation

### Tutoriales Recomendados

- **gRPC en Python:** https://grpc.io/docs/languages/python/quickstart/
- **gRPC en C++:** https://grpc.io/docs/languages/cpp/quickstart/
- **KMP Algorithm:** https://www.geeksforgeeks.org/kmp-algorithm-for-pattern-searching/
- **Boyer-Moore:** https://www.geeksforgeeks.org/boyer-moore-algorithm-for-pattern-searching/

### Papers Académicos

- Knuth, D. E., Morris, J. H., & Pratt, V. R. (1977). "Fast pattern matching in strings"
- Boyer, R. S., & Moore, J. S. (1977). "A fast string searching algorithm"

### Datasets de Prueba

- **NCBI GenBank:** https://www.ncbi.nlm.nih.gov/genbank/
- **Ensembl Genomes:** https://ensembl.org/
- **1000 Genomes Project:** https://www.internationalgenome.org/

### Herramientas de Desarrollo

- **Visual Studio Code:** Editor recomendado
- **PyCharm:** IDE para Python
- **CLion:** IDE para C++
- **Postman:** Testing de API
- **Docker Desktop:** Containerización
- **DBeaver:** Cliente de PostgreSQL
- **Redis Insight:** Cliente de Redis

---

## MÉTRICAS DE ÉXITO

### Métricas Técnicas

1. **Rendimiento:**
   - Búsquedas en secuencias <1M nucleótidos completan en <5 segundos (90th percentile)
   - Carga de archivos 100MB completa en <1 minuto
   - Latencia gRPC <100ms para búsquedas simples

2. **Escalabilidad:**
   - Sistema soporta 10 usuarios concurrentes sin degradación
   - Throughput de al menos 100 búsquedas/hora

3. **Confiabilidad:**
   - Disponibilidad >99% durante pruebas
   - Tasa de error <1% de requests
   - Recovery time <30 segundos después de fallo

4. **Calidad de Código:**
   - Cobertura de tests >80%
   - 0 vulnerabilidades críticas (escaneo con Bandit/cppcheck)
   - Complejidad ciclomática <10 en funciones críticas

### Métricas de Proyecto

1. **Cronograma:**
   - Completar v1.0 en 13 semanas
   - Entrega de hitos según planificación

2. **Documentación:**
   - Documentación de arquitectura completa
   - Guía de usuario con al menos 5 ejemplos
   - API documentation 100% completa

3. **Alcance:**
   - Todas las funcionalidades de v1.0 implementadas
   - Máximo 10% de scope creep

---

## GLOSARIO DE TÉRMINOS

**ADN (Ácido Desoxirribonucleico):** Molécula que contiene la información genética. Compuesta por secuencias de cuatro nucleótidos: Adenina (A), Timina (T), Citosina (C) y Guanina (G).

**Algoritmo de Búsqueda de Patrones:** Algoritmo que encuentra todas las ocurrencias de un patrón dentro de un texto más largo.

**Boyer-Moore:** Algoritmo de búsqueda de cadenas que utiliza dos heurísticas (mal carácter y buen sufijo) para saltar posiciones durante la búsqueda.

**Circuit Breaker:** Patrón de diseño que previene que un sistema intente ejecutar una operación que probablemente fallará.

**Coincidencia Directa:** Ocurrencias de un patrón que no comparten nucleótidos entre sí.

**gRPC:** Framework de llamadas a procedimientos remotos de alto rendimiento desarrollado por Google.

**KMP (Knuth-Morris-Pratt):** Algoritmo de búsqueda de cadenas que utiliza una tabla de prefijos para evitar comparaciones redundantes.

**Microservicio:** Servicio pequeño e independiente que forma parte de una arquitectura más grande.

**Microsatélite:** Secuencia corta de ADN repetida en tándem.

**Nucleótido:** Unidad básica del ADN (A, T, C, o G).

**ORF (Open Reading Frame):** Marco de lectura abierto, secuencia que potencialmente codifica una proteína.

**Patrón:** Subsecuencia específica que se busca dentro de una secuencia mayor.

**Protocol Buffers:** Método de serialización de datos estructurados desarrollado por Google.

**Secuencia de ADN:** Cadena de nucleótidos que representa información genética.

**Sitio de Restricción:** Secuencia específica de ADN reconocida y cortada por una enzima de restricción.

**Solapamiento:** Cuando las ocurrencias de un patrón comparten nucleótidos entre sí.

**STR (Short Tandem Repeat):** Repetición corta en tándem, tipo de microsatélite.

---

## PREGUNTAS FRECUENTES (FAQ)

**P: ¿Por qué usar C++ para el motor de búsqueda en lugar de Python?**
R: C++ ofrece rendimiento significativamente superior para operaciones computacionalmente intensivas como búsqueda de patrones en secuencias de millones de nucleótidos. Los algoritmos en C++ pueden ser 10-100x más rápidos que implementaciones equivalentes en Python.

**P: ¿Por qué no usar una base de datos especializada en bioinformática?**
R: Para v1.0, PostgreSQL es suficiente y más familiar para la mayoría de desarrolladores. Bases de datos especializadas como BioSQL pueden considerarse en versiones futuras si el volumen de datos lo justifica.

**P: ¿Cuál es la diferencia práctica entre coincidencia directa y solapamiento?**
R: Coincidencia directa es útil para buscar genes o sitios funcionales que no se superponen. Solapamiento es crucial para detectar repeticiones como microsatélites o expansiones de trinucleótidos relacionadas con enfermedades genéticas.

**P: ¿Por qué no implementar autenticación desde v1.0?**
R: Para reducir complejidad inicial y permitir demostración rápida. El uso de localStorage permite funcionalidad de historial sin overhead de gestión de usuarios. Autenticación se agregará en v1.2 como feature opcional.

**P: ¿Cómo manejo secuencias más grandes que 100MB?**
R: En v1.0, el límite es 100MB. Para secuencias mayores, considerar: (1) dividir archivo en múltiples secuencias, (2) esperar v1.2 que soportará streaming sin límite estricto, o (3) procesar offline y cargar solo resultados relevantes.

**P: ¿Qué pasa si el microservicio C++ falla durante una búsqueda?**
R: El Circuit Breaker en Django detecta el fallo, retorna error amigable al usuario, y previene que nuevas búsquedas saturen el servicio mientras se recupera. Si la búsqueda era asíncrona, el job se marca como FAILED con mensaje de error.

**P: ¿Cómo se garantiza que los algoritmos son correctos?**
R: Mediante: (1) suite exhaustiva de tests unitarios con casos conocidos, (2) comparación con implementaciones de referencia, (3) validación con datasets biológicos reales de GenBank, (4) benchmarking contra búsqueda naive en modo de prueba.

**P: ¿Cuánta memoria consume el sistema para secuencias grandes?**
R: El microservicio C++ puede usar hasta ~512MB por búsqueda. Django usa memoria principalmente para caché. PostgreSQL almacena secuencias con compresión. Total estimado para deployment: 4-8GB RAM.

**P: ¿Se puede usar para buscar en múltiples secuencias simultáneamente?**
R: En v1.0, cada búsqueda es sobre una secuencia. Para buscar en múltiples secuencias, se debe llamar a la API múltiples veces (puede ser en paralelo desde el cliente). Búsqueda batch podría agregarse en v1.1.

---

Este documento contiene toda la información necesaria para entender, implementar y mantener el sistema. Puede ser utilizado como referencia completa para desarrollo o como contexto para otros LLMs.