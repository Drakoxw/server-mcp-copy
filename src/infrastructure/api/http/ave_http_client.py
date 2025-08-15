import httpx
from typing import Any, Tuple, Union

class AveHttpClient:
    def __init__(self, token: str, timeout: int=10):
        self.timeout = timeout
        self._client = httpx.AsyncClient(
            headers={
                "Authorization": token,
                "Content-Type": "application/json"
            },
            timeout=self.timeout
        )

    def setToken(self, token: str, timeout: int=10):
        return AveHttpClient(token, timeout)

    async def post(self, url: str, json: Union[dict, list]) -> Tuple[int, Any]:
        try:
            response = await self._client.post(url, json=json)
            status = response.status_code
            try:
                data = response.json()
            except Exception:
                data = {"error": "Invalid JSON in response"}
            return status, data
        except httpx.RequestError as e:
            return 500, {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return 500, {"error": f"Unexpected error: {str(e)}"}
        

    async def get(self, url: str, params: dict = {}) -> Tuple[int, Any]:
        try:
            response = await self._client.get(url, params=params)
            status = response.status_code
            try:
                data = response.json()
            except Exception:
                data = {"error": "Invalid JSON in response"}
            return status, data
        except httpx.RequestError as e:
            return 500, {"error": f"Request failed: {str(e)}"}
        except Exception as e:
            return 500, {"error": f"Unexpected error: {str(e)}"}
        
    async def close(self):
        await self._client.aclose()

