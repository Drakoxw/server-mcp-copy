from fastmcp.server.dependencies import get_http_headers
import socket

class IpTool:
    def __init__(self):
        pass

    def get_ip(self):
        headers = get_http_headers()
        return (
            headers.get("x-forwarded-for", "").split(",")[0].strip() or
            headers.get("x-real-ip", "") or
            headers.get("cf-connecting-ip", "") or
            headers.get("x-client-ip", "") or
            headers.get("x-forwarded", "") or
            headers.get("forwarded-for", "") or
            headers.get("forwarded", "") or
            "Unknown"
        )

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # No hace conexión real, solo obtiene IP usada para salir
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip