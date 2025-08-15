import httpx
import time
from src.infrastructure.api.http.ave_http_client import AveHttpClient
from src.infrastructure.config.common_config import CommonConfig
from src.infrastructure.session.user_session import AveSession
from src.tools.base.crypter import Crypter

TOKEN_TIME = int(CommonConfig.TOKEN_LIFE_TIME_HOURS.value)

class AveOnlineAuth:
    def __init__(self):
        pass

    async def login(self, username: str, password: str) -> dict:
        """Inicio de sesión en AveOnline, devolverá un objeto con los datos de la sesión."""

        resp = {
            "error": True,
            "message": "Error desconocido",
            "data": {}
        }

        if not username or not password:
            resp["message"] = "Por favor, proporciona un nombre de usuario y una contraseña."
            return resp

        json_payload = {
            "tipo": "AuthProduct",
            "user": username,
            "password": password,
            "tokenTime": TOKEN_TIME,
        }

        url = "https://app.aveonline.co/api/auth/v3.0/index.php"

        headers = {
            "User-Agent": "AveMCP/1.0",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        async with httpx.AsyncClient(timeout=5, headers=headers) as client:
            try:
                response = await client.post(url, json=json_payload)
                response.raise_for_status()
                data = response.json()

                if data.get("status") == "ok":
                    data_session = data.get("data")
                    ave = AveSession(
                        id=int(data_session.get("id")),
                        document=int(data_session.get("document")),
                        user=str(data_session.get("user")),
                        name=str(data_session.get("name")),
                        email=str(data_session.get("email")),
                        razon=str(data_session.get("razon")),
                        idEnterprise=int(data_session.get("idEnterprise")),
                        accessRedirect=str(data_session.get("accessRedirect")),
                        token=str(data_session.get("token")),
                        tokenBody=str(data_session.get("tokenBody")),
                        logisticAdvisorContactNumber=str(data_session.get("logisticAdvisorContactNumber")),
                    )
                    resp["error"] = False
                    resp["message"] = "Inicio de sesión exitoso"
                    resp["data"] = ave
                else:
                    resp["message"] = "Error en el inicio de sesión: " + data.get("message", "No se pudo iniciar sesión.")

            except httpx.HTTPStatusError as e:
                resp["message"] = f"Error HTTP: {str(e)}"
            except httpx.RequestError as e:
                resp["message"] = f"Error de conexión: {str(e)}"
            except Exception as e:
                resp["message"] = f"Error inesperado: {str(e)}"

        return resp


    async def loginOAuth(self, email: str) -> dict:
        """Inicio de sesión en AveOnline, devolverá un objeto con los datos de la sesión."""

        resp = {
            "error": True,
            "message": "Error desconocido",
            "data": {}
        }

        timeEncript =  Crypter.encrypt_aes(str(time.time()))
        emailEncrypt = Crypter.encrypt_aes(email)

        json_payload = {
            "tipo": "OauthProduct",
            "emailEncrypt": emailEncrypt,
            "timeEncript": timeEncript,
            "tokenTime": TOKEN_TIME,
            "method": "AES",
        }

        url = "https://app.aveonline.co/api/auth/v3.0/index.php"

        try:
            client = AveHttpClient("")
            _, response = await client.post(url, json=json_payload)

            if response.get("status") == "ok":
                data_session = response['data']
                ave = AveSession(
                    id=int(data_session.get("id")),
                    document=int(data_session.get("document")),
                    user=str(data_session.get("user")),
                    name=str(data_session.get("name")),
                    email=str(data_session.get("email")),
                    razon=str(data_session.get("razon")),
                    idEnterprise=int(data_session.get("idEnterprise")),
                    accessRedirect=str(data_session.get("accessRedirect")),
                    token=str(data_session.get("token")),
                    tokenBody=str(data_session.get("tokenBody")),
                    logisticAdvisorContactNumber=str(data_session.get("logisticAdvisorContactNumber")),
                )
                resp["error"] = False
                resp["message"] = "Inicio de sesión exitoso"
                resp["data"] = ave
            else:
                resp["message"] = "Error en el inicio de sesión: " + response.get("message", "No se pudo iniciar sesión.")

        except httpx.HTTPStatusError as e:
            resp["message"] = f"Error HTTP: {str(e)}"
        except httpx.RequestError as e:
            resp["message"] = f"Error de conexión: {str(e)}"
        except Exception as e:
            resp["message"] = f"Error inesperado: {str(e)}"

        return resp
