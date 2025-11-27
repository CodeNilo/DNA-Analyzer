# DNA Sequence Pattern Matching System

Web application for searching patterns in DNA sequences using optimized algorithms. Built with Django and a C++ gRPC microservice for high-performance pattern matching.

## Architecture

The system uses a microservices architecture with two main components:

- **Django Backend**: Manages HTTP requests, data validation, business logic, and orchestrates the search operations
- **C++ gRPC Microservice**: Executes pattern matching algorithms (KMP and Boyer-Moore) for maximum performance

### Stack

- Backend: Django 5.x, Django REST Framework, PostgreSQL/SQLite
- Microservice: C++17, gRPC, Protocol Buffers
- Frontend: JavaScript ES6+, CSS3, Django templates
- Async Processing: Celery, Redis
- Testing: pytest, Google Test

### Project Structure

```
backend/
├── config/              # Django settings and configuration
├── sequences_api/       # Sequence upload and management
├── search_api/          # Pattern search and gRPC client
└── tests/              # Integration and E2E tests

microservices/dna_search/
├── src/                # C++ source files
│   └── algorithms/     # KMP and Boyer-Moore implementations
├── proto/              # Protocol Buffer definitions
└── tests/              # C++ unit tests

frontend/
├── templates/          # HTML templates
└── static/             # JS and CSS
```

## Quick Start

### Backend Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt

cd backend
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

The app runs at http://localhost:8000 using SQLite by default.

### gRPC Microservice (Docker)

```powershell
cd microservices/dna_search
docker build -t dna-search .
docker run --rm -p 50051:50051 dna-search
```

Custom port:
```powershell
docker run --rm -e GRPC_PORT=6000 -p 6000:6000 dna-search
```

Update `GRPC_PORT` in `backend/config/settings.py` if you change the port.

### Building from Source (without Docker)

Requires: CMake 3.20+, C++17 compiler, gRPC and Protobuf libraries

```bash
cd microservices/dna_search
mkdir build && cd build
cmake ..
make
./dna_search_server
```

## Testing

```powershell
cd backend
python run_tests.py                 # All tests with coverage
python run_tests.py --unit          # Unit tests only
python run_tests.py --integration   # Integration tests
python run_tests.py --module sequences
```

C++ microservice tests:
```bash
cd microservices/dna_search/build
make test
```

## Features

- Upload DNA sequences via CSV (up to 100MB)
- Pattern search with KMP and Boyer-Moore algorithms
- Two modes: direct matching and overlapping matches
- Async processing for large sequences
- Result caching with Redis
- Search history stored in localStorage
- Export results as CSV or JSON

## API Endpoints

**Sequences**
- `POST /api/sequences/upload/` - Upload DNA sequence
- `GET /api/sequences/` - List sequences

**Search**
- `POST /api/search/` - Search pattern
- `GET /api/search/jobs/{id}/` - Get search results

## Configuration

Edit `backend/config/settings.py`:

```python
GRPC_HOST = 'localhost'
GRPC_PORT = '50051'
MAX_UPLOAD_SIZE = 100 * 1024 * 1024  # 100MB
```

## Limitations

- Max upload: 100MB
- Max results: 100,000 matches per query
- History: 50 searches in localStorage
- Sync search timeout: 30 seconds

## Commands

```powershell
python manage.py createsuperuser
python manage.py shell
python manage.py collectstatic
```
