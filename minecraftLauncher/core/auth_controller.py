import requests
from config.manager import config

class AuthController:
    def __init__(self):
        api_url = config.get("api_url")
        if not api_url:
            ip = config.get("server_ip", "127.0.0.1")
            port = config.get("server_port", 8000)
            api_url = f"http://{ip}:{port}/api/v1"
        self.api_url = api_url

    def login_no_premium(self, username, password):
        url = f"{self.api_url}/auth/login"
        payload = {"username": username, "password": password}
        try:
            response = requests.post(url, json=payload, timeout=10)
            if response.status_code == 200:
                return {"status": "OK", "data": response.json()}
            return {"status": "ERROR", "message": response.json().get("detail", "Invalid credentials.")}
        except requests.exceptions.ConnectionError:
            return {"status": "ERROR", "message": "Cannot connect to authentication server."}
