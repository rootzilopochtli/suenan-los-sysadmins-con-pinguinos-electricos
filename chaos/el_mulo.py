from locust import HttpUser, task, between

class ElMulo(HttpUser):
    # Tiempos de espera casi nulos para simular un ataque de denegación (DDoS)
    wait_time = between(0.1, 0.5)

    @task(3)
    def index_page(self):
        """Asedia la página principal (Dashboard estático)"""
        # Se detiene en la Capa 2 (Nginx)
        self.client.get("/")

    @task(7)
    def status_db_endpoint(self):
        """Asedia el backend y la base de datos"""
        # Atraviesa el Proxy (Capa 2), golpea a FastAPI (Capa 3) y estresa a Términus (Capa 4)
        with self.client.get("/api/status/db", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Falla detectada. HTTP {response.status_code}")
