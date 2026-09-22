from locust import HttpUser, task, between
import requests

class ElMuloNerfeado(HttpUser):
    wait_time = between(0.1, 0.5)

    @task(3)
    def index_page(self):
        """Tráfico legítimo simulado."""
        self.client.get("/")

    @task(7)
    def escaneo_hostil(self):
        """Ataque determinista: Fuerza errores 404 buscando rutas sensibles."""
        with self.client.get("/api/admin/dump", catch_response=True) as response:
            if response.status_code == 404:
                # Locust lo marca como éxito internamente para no ensuciar la salida de terminal,
                # pero Nginx registrará el 404 y Agatha actuará de inmediato.
                response.success()
            else:
                response.failure(f"Código inesperado: {response.status_code}")

