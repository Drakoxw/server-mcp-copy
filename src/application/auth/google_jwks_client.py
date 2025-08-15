
import time

import httpx
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"

class GoogleJWKSClient:
    """Cliente para obtener y cachear las claves públicas de Google"""
    
    def __init__(self):
        self.jwks_cache = None
        self.cache_expires = 0

    def get_jwks_url(self):
        return GOOGLE_JWKS_URL

    async def get_jwks(self):
        """Obtiene las claves públicas de Google, usando cache si está disponible"""
        current_time = time.time()
        
        # Verificar si el cache sigue válido (Google recomienda cachear por 24 horas)
        if self.jwks_cache and current_time < self.cache_expires:
            return self.jwks_cache
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(GOOGLE_JWKS_URL)
                
                if response.status_code == 200:
                    self.jwks_cache = response.json()
                    # Cachear por 1 hora
                    self.cache_expires = current_time + 3600
                    return self.jwks_cache
                else:
                    return None
                    
        except Exception as e:
            return None
    
    def get_key_by_kid(self, jwks, kid):
        """Busca una clave específica por su Key ID"""
        if not jwks or 'keys' not in jwks:
            return None
            
        for key in jwks['keys']:
            if key.get('kid') == kid:
                return key
        return None

