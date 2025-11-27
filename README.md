App Django + DRF para analizar secuencias y un microservicio gRPC en C++ para búsqueda de patrones.

## Requisitos
- Python 3.12+ y pip
- Docker (para el microservicio gRPC). Si lo prefieres sin Docker: CMake, toolchain C++17, gRPC y Protobuf instalados.

## Backend Django (dev)
```powershell
# Desde la raíz del repo
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt

cd backend
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```
Notas: usa SQLite en `backend/db.sqlite3`. El cliente gRPC usa `GRPC_HOST`/`GRPC_PORT` definidos en `config/settings.py` (por defecto `localhost:50051`).

## Tests
```powershell
cd backend
.\.venv\Scripts\Activate
python run_tests.py                 # todos los tests con coverage
python run_tests.py --unit          # solo unitarios
python run_tests.py --integration   # solo integracion
python run_tests.py --module sequences
python run_tests.py --coverage --parallel
# También vale: pytest
```

## Microservicio gRPC via Docker
```powershell
cd microservices/dna_search
docker build -t dna-search .
docker run --rm -p 50051:50051 dna-search                   # puerto por defecto
docker run --rm -e GRPC_PORT=6000 -p 6000:6000 dna-search   # puerto custom
```
El backend se conecta a `localhost:50051`; si cambias el puerto, ajústalo en `config/settings.py`.

## Comandos útiles de Django
```powershell
python manage.py createsuperuser
python manage.py shell
python manage.py collectstatic
```