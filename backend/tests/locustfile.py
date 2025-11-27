"""
Pruebas de carga usando Locust

Para ejecutar:
    locust -f backend/tests/locustfile.py --host=http://localhost:8000

Luego abrir http://localhost:8089 para la interfaz web

Escenarios:
- Upload de secuencias
- Búsqueda de patrones
- Listado de secuencias
- Carga mixta
"""

import json
import io
import random
from locust import HttpUser, task, between, SequentialTaskSet


class SequenceUploadTasks(SequentialTaskSet):
    """
    Escenario: Usuario sube una secuencia y luego busca en ella
    """

    def on_start(self):
        """Setup: preparar datos"""
        self.sequence_id = None
        self.patterns = ["ATG", "TGA", "TAA", "TAG", "TATA", "GATTACA"]

    @task
    def upload_sequence(self):
        """Upload de secuencia pequeña"""
        sequence_data = "ATCG" * 250  # 1kb
        file_content = sequence_data.encode('utf-8')

        files = {
            'file': ('test_sequence.txt', io.BytesIO(file_content), 'text/plain')
        }
        data = {
            'name': f'load_test_seq_{random.randint(1000, 9999)}'
        }

        with self.client.post(
            '/api/sequences/upload/',
            files=files,
            data=data,
            catch_response=True
        ) as response:
            if response.status_code == 201:
                self.sequence_id = response.json()['id']
                response.success()
            elif response.status_code == 200:
                # Duplicado - también válido
                self.sequence_id = response.json()['id']
                response.success()
            else:
                response.failure(f"Failed to upload: {response.status_code}")

    @task(3)
    def search_pattern(self):
        """Buscar patrón en la secuencia subida"""
        if not self.sequence_id:
            return

        pattern = random.choice(self.patterns)

        with self.client.post(
            '/api/search/',
            json={
                'sequence_id': self.sequence_id,
                'pattern': pattern,
                'allow_overlapping': random.choice([True, False])
            },
            headers={'Content-Type': 'application/json'},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if 'job' in data and 'results' in data:
                    response.success()
                else:
                    response.failure("Invalid response format")
            else:
                response.failure(f"Search failed: {response.status_code}")


class BrowsingUser(HttpUser):
    """
    Usuario que solo navega y consulta (sin uploads)
    """
    wait_time = between(1, 3)

    @task(5)
    def list_sequences(self):
        """Listar secuencias"""
        page = random.randint(1, 3)
        with self.client.get(
            f'/api/sequences/?page={page}',
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to list: {response.status_code}")

    @task(1)
    def view_job_detail(self):
        """Ver detalle de un job (si existe)"""
        # Asumir que hay jobs con IDs 1-100
        job_id = random.randint(1, 100)
        with self.client.get(
            f'/api/search/jobs/{job_id}/',
            catch_response=True
        ) as response:
            if response.status_code in [200, 404]:
                # 404 es esperado si el job no existe
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")


class UploadUser(HttpUser):
    """
    Usuario que sube secuencias frecuentemente
    """
    wait_time = between(2, 5)

    @task
    def upload_small_sequence(self):
        """Upload de secuencia pequeña (1kb)"""
        sequence_data = "ATCG" * 250
        file_content = sequence_data.encode('utf-8')

        files = {
            'file': ('small_seq.txt', io.BytesIO(file_content), 'text/plain')
        }

        with self.client.post(
            '/api/sequences/upload/',
            files=files,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Upload failed: {response.status_code}")

    @task
    def upload_medium_sequence(self):
        """Upload de secuencia mediana (10kb)"""
        sequence_data = "ATCG" * 2500
        file_content = sequence_data.encode('utf-8')

        files = {
            'file': ('medium_seq.txt', io.BytesIO(file_content), 'text/plain')
        }

        with self.client.post(
            '/api/sequences/upload/',
            files=files,
            catch_response=True
        ) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"Upload failed: {response.status_code}")


class SearchHeavyUser(HttpUser):
    """
    Usuario que hace muchas búsquedas
    """
    wait_time = between(0.5, 2)

    def on_start(self):
        """Setup: crear una secuencia para buscar"""
        sequence_data = "ATCG" * 1000  # 4kb
        file_content = sequence_data.encode('utf-8')

        files = {
            'file': ('search_test.txt', io.BytesIO(file_content), 'text/plain')
        }

        response = self.client.post(
            '/api/sequences/upload/',
            files=files
        )

        if response.status_code in [200, 201]:
            self.sequence_id = response.json()['id']
        else:
            self.sequence_id = 1  # Fallback

    @task(10)
    def search_common_pattern(self):
        """Buscar patrones comunes"""
        patterns = ["ATG", "TAA", "TGA", "TAG"]
        pattern = random.choice(patterns)

        with self.client.post(
            '/api/search/',
            json={
                'sequence_id': self.sequence_id,
                'pattern': pattern
            },
            headers={'Content-Type': 'application/json'},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Search failed: {response.status_code}")

    @task(2)
    def search_long_pattern(self):
        """Buscar patrón más largo"""
        patterns = ["ATGATG", "TATAA", "GATTACA"]
        pattern = random.choice(patterns)

        with self.client.post(
            '/api/search/',
            json={
                'sequence_id': self.sequence_id,
                'pattern': pattern,
                'allow_overlapping': True
            },
            headers={'Content-Type': 'application/json'},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Search failed: {response.status_code}")


class MixedWorkloadUser(HttpUser):
    """
    Usuario con carga de trabajo mixta (realista)
    """
    wait_time = between(1, 4)
    tasks = [SequenceUploadTasks]

    @task(3)
    def list_sequences(self):
        """Listar secuencias ocasionalmente"""
        self.client.get('/api/sequences/')


class StressTestUser(HttpUser):
    """
    Usuario para pruebas de estrés (sin espera entre requests)
    """
    wait_time = between(0, 0.5)

    @task
    def rapid_fire_search(self):
        """Búsquedas rápidas consecutivas"""
        with self.client.post(
            '/api/search/',
            json={
                'sequence_id': 1,  # Asumir que existe
                'pattern': 'ATG'
            },
            headers={'Content-Type': 'application/json'},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 400:
                # Sequence no existe, pero request fue procesado
                response.success()
            else:
                response.failure(f"Failed: {response.status_code}")


# Configuraciones de escenarios

class NormalLoadTest(HttpUser):
    """
    Carga normal: 70% búsquedas, 20% navegación, 10% uploads
    """
    wait_time = between(2, 5)

    @task(7)
    def search(self):
        self.client.post(
            '/api/search/',
            json={'sequence_id': random.randint(1, 10), 'pattern': 'ATG'},
            headers={'Content-Type': 'application/json'}
        )

    @task(2)
    def browse(self):
        self.client.get('/api/sequences/')

    @task(1)
    def upload(self):
        sequence_data = "ATCG" * 250
        files = {
            'file': ('test.txt', io.BytesIO(sequence_data.encode('utf-8')), 'text/plain')
        }
        self.client.post('/api/sequences/upload/', files=files)


class PeakLoadTest(HttpUser):
    """
    Carga pico: Muchos usuarios simultáneos con espera mínima
    """
    wait_time = between(0.5, 1.5)

    @task(5)
    def search(self):
        self.client.post(
            '/api/search/',
            json={'sequence_id': 1, 'pattern': random.choice(['ATG', 'TAA', 'TGA'])},
            headers={'Content-Type': 'application/json'}
        )

    @task(3)
    def list(self):
        self.client.get('/api/sequences/')

    @task(2)
    def upload(self):
        sequence_data = "ATCG" * 100
        files = {
            'file': ('test.txt', io.BytesIO(sequence_data.encode('utf-8')), 'text/plain')
        }
        self.client.post('/api/sequences/upload/', files=files)


# Para ejecutar escenarios específicos:
# locust -f locustfile.py NormalLoadTest --host=http://localhost:8000
# locust -f locustfile.py PeakLoadTest --host=http://localhost:8000
# locust -f locustfile.py StressTestUser --host=http://localhost:8000
