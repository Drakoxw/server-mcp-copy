"""
Servicio para autenticación con Google con OAuth - Versión Multi-Usuario
"""
import asyncio
import os
import webbrowser
import secrets
import jwt
import uuid
from datetime import datetime
import time
from threading import Thread
import uvicorn
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from authlib.integrations.httpx_client import AsyncOAuth2Client
from authlib.oauth2.rfc7636 import create_s256_code_challenge
from src.tools.logger_config import LoggerSetup
import httpx
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
CALLBACK_SERVER_PORT = int(os.getenv("CALLBACK_SERVER_PORT", 3030))
REDIRECT_URI = os.getenv("REDIRECT_URI", "127.0.0.1")
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
SCOPE = "openid email profile"

auth_logger = LoggerSetup(file_name="google-ouath-multi.log").create_module_logger("auth")

# Servidor FastAPI global para callbacks
app = FastAPI(title="OAuth Callback Server")
oauth_sessions = {}
callback_server = None
class GoogleJWKSClient:
    """Cliente para obtener y cachear las claves públicas de Google"""
    
    def __init__(self):
        self.jwks_cache = None
        self.cache_expires = 0
        
    async def get_jwks(self):
        """Obtiene las claves públicas de Google, usando cache si está disponible"""
        current_time = time.time()
        
        if self.jwks_cache and current_time < self.cache_expires:
            return self.jwks_cache
            
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(GOOGLE_JWKS_URL)
                
                if response.status_code == 200:
                    self.jwks_cache = response.json()
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

# Instancia global del cliente JWKS
jwks_client = GoogleJWKSClient()

@app.get("/callback/{session_id}")
async def oauth_callback(
    session_id: str, 
    code: str = Query(None), 
    error: str = Query(None),
    state: str = Query(None)
):
    """Endpoint para manejar callbacks de OAuth por sesión"""
    
    if session_id not in oauth_sessions:
        return HTMLResponse("""
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>❌ Sesión no encontrada</h1>
                <p>La sesión de OAuth no existe o ha expirado.</p>
            </body>
        </html>
        """, status_code=404)
    
    # Actualizar la sesión con los resultados
    session_data = oauth_sessions[session_id]
    session_data['code'] = code
    session_data['error'] = error
    session_data['completed'] = True
    
    if error:
        return HTMLResponse(f"""
        <html>
            <head><title>Error de Autorización</title></head>
            <body>
                <h1>❌ Error en la autorización</h1>
                <p><strong>Error:</strong> {error}</p>
                <p>Puedes cerrar esta ventana.</p>
            </body>
        </html>
        """)
    else:
        return HTMLResponse("""
        <html>
            <head><title>Autorización Exitosa</title></head>
            <body>
                <h1>✅ ¡Autorización exitosa!</h1>
                <p>Ya puedes cerrar esta ventana.</p>
                <script>
                    setTimeout(() => window.close(), 3000);
                </script>
            </body>
        </html>
        """)

@app.get("/sessions")
async def get_sessions():
    """Endpoint para debuggear sesiones activas"""
    return {
        "active_sessions": len(oauth_sessions),
        "sessions": {
            session_id: {
                "completed": data["completed"],
                "has_code": data["code"] is not None,
                "has_error": data["error"] is not None,
                "created_at": data["created_at"]
            }
            for session_id, data in oauth_sessions.items()
        }
    }

def start_callback_server():
    """Inicia el servidor de callbacks en un hilo separado"""
    global callback_server
    if callback_server is None:
        def run_server():
            uvicorn.run(app, host=REDIRECT_URI, port=CALLBACK_SERVER_PORT, log_level="warning")
        
        callback_server = Thread(target=run_server, daemon=True)
        callback_server.start()
        
        # Esperar un poco para que el servidor se inicie
        import time
        time.sleep(2)

async def validate_jwt_signature(id_token, client_id):
    """Valida la firma del JWT ID Token usando las claves públicas de Google"""
    try:
        # 1. Decodificar el header del JWT para obtener el 'kid' (Key ID)
        header = jwt.get_unverified_header(id_token)
        kid = header.get('kid')
        
        if not kid:
            return {'valid': False, 'error': 'Token JWT no contiene Key ID (kid) en el header'}
            
        # 2. Obtener las claves públicas de Google        
        jwks = await jwks_client.get_jwks()
        if not jwks:
            return {'valid': False, 'error': 'No se pudieron obtener las claves públicas de Google'}
        
        key_data = jwks_client.get_key_by_kid(jwks, kid)
        if not key_data:
            return {'valid': False, 'error': f'No se encontró la clave pública para kid: {kid}'}
        
        # 3. Validar la firma con tolerancia de tiempo (clock skew)
        public_key = jwt.PyJWK(key_data).key
        
        try:
            # CORRECCIÓN: Agregar leeway para manejar diferencias de tiempo entre servidores
            payload = jwt.decode(
                id_token,
                public_key,
                algorithms=['RS256'],
                audience=client_id,
                issuer='https://accounts.google.com',
                leeway=60,  # Tolerancia de 30 segundos para diferencias de reloj
                options={
                    'verify_exp': True,
                    'verify_aud': True,
                    'verify_iss': True,
                    'verify_iat': True,  # Verificar issued_at con tolerancia
                }
            )
                        
            return {
                'valid': True,
                'payload': payload,
                'validation_details': {
                    'algorithm': header.get('alg'),
                    'key_id': kid,
                    'issuer': payload.get('iss'),
                    'audience': payload.get('aud'),
                    'subject': payload.get('sub'),
                    'issued_at': datetime.fromtimestamp(payload.get('iat', 0)),
                    'expires_at': datetime.fromtimestamp(payload.get('exp', 0)),
                    'email_verified': payload.get('email_verified', False),
                    'leeway_applied': True,  # Indicador de que se aplicó tolerancia
                    'leeway_seconds': 30
                }
            }
            
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token JWT ha expirado'}
        except jwt.InvalidAudienceError:
            return {'valid': False, 'error': 'Audiencia del token JWT inválida'}
        except jwt.InvalidIssuerError:
            return {'valid': False, 'error': 'Emisor del token JWT inválido'}
        except jwt.InvalidSignatureError:
            return {'valid': False, 'error': 'Firma del token JWT inválida'}
        except jwt.ImmatureSignatureError:
            # CORRECCIÓN: Manejo específico del error "iat" (token no válido aún)
            return {'valid': False, 'error': 'Token emitido en el futuro - sincronizar relojes del servidor'}
        except jwt.InvalidIssuedAtError:
            return {'valid': False, 'error': 'Timestamp iat (issued at) inválido en el token'}
        except Exception as e:
            return {'valid': False, 'error': f'Error validando JWT: {str(e)}'}
            
    except Exception as e:
        return {'valid': False, 'error': f'Error procesando token JWT: {str(e)}'}

async def validate_and_get_user_info_secure(token, client_id):
    """Versión segura que valida la firma JWT antes de usar los datos"""
    user_data = {}
    
    try:
        # 1. VALIDACIÓN SEGURA DEL ID TOKEN
        if 'id_token' in token:
            jwt_validation = await validate_jwt_signature(token['id_token'], client_id)
            # auth_logger.info(f"jwt_validation: {jwt_validation}")
            
            if jwt_validation['valid']:
                user_data['id_token_data'] = {
                    'user_id': jwt_validation['payload'].get('sub'),
                    'email': jwt_validation['payload'].get('email'),
                    'email_verified': jwt_validation['payload'].get('email_verified'),
                    'name': jwt_validation['payload'].get('name'),
                    'picture': jwt_validation['payload'].get('picture'),
                    'given_name': jwt_validation['payload'].get('given_name'),
                    'family_name': jwt_validation['payload'].get('family_name'),
                    'locale': jwt_validation['payload'].get('locale'),
                    'issued_at': jwt_validation['validation_details']['issued_at'],
                    'expires_at': jwt_validation['validation_details']['expires_at'],
                    'audience': jwt_validation['payload'].get('aud'),
                    'issuer': jwt_validation['payload'].get('iss'),
                }
                user_data['jwt_validation'] = jwt_validation['validation_details']
                user_data['jwt_validation']['signature_valid'] = True
            else:
                user_data['jwt_validation'] = {
                    'signature_valid': False,
                    'error': jwt_validation['error']
                }
                
        # 2. Llamada a la API de Google UserInfo (como respaldo)
        if 'access_token' in token:
            async with httpx.AsyncClient() as client:
                headers = {'Authorization': f"Bearer {token['access_token']}"}
                response = await client.get(USERINFO_URL, headers=headers)
                
                if response.status_code == 200:
                    user_data['api_data'] = response.json()
                else:
                    user_data['api_error'] = {
                        'status_code': response.status_code,
                        'error': response.text
                    }
        
        # 3. Validación del access token
        async with httpx.AsyncClient() as client:
            validate_url = f"https://oauth2.googleapis.com/tokeninfo?access_token={token['access_token']}"
            response = await client.get(validate_url)
            
            if response.status_code == 200:
                token_info = response.json()
                user_data['token_validation'] = {
                    'valid': True,
                    'scope': token_info.get('scope'),
                    'audience': token_info.get('aud'),
                    'expires_in': token_info.get('expires_in'),
                }
                # auth_logger.info(f"token_validation: {user_data['token_validation']}")
            else:
                user_data['token_validation'] = {
                    'valid': False,
                    'error': response.text
                }
        
        return user_data
        
    except Exception as e:
        return {'error': str(e)}

async def run_google_pkce_auth_secure_multiuser():
    """Versión multi-usuario de autenticación OAuth con PKCE"""
    
    # 1. Asegurar que el servidor de callbacks esté ejecutándose
    start_callback_server()
    
    # 2. Generar ID único para esta sesión
    session_id = str(uuid.uuid4())
    
    # 3. Configurar redirect URI específico para esta sesión
    redirect_uri = f"http://{REDIRECT_URI}:{CALLBACK_SERVER_PORT}/callback/{session_id}"
    
    # 4. Crear entrada de sesión
    oauth_sessions[session_id] = {
        'code': None,
        'error': None,
        'completed': False,
        'created_at': datetime.now().isoformat(),
        'redirect_uri': redirect_uri
    }

    # auth_logger.info(f"Redirect URI: {redirect_uri}")
    # auth_logger.info(f"oauth_sessions[session_id] : {oauth_sessions[session_id] }")

    
    try:
        # 5. Crear code_verifier y code_challenge
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = create_s256_code_challenge(code_verifier)

        # 6. Crear cliente OAuth2 con PKCE
        client = AsyncOAuth2Client(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=redirect_uri
        )

        # 7. Crear la URL de autorización
        auth_url = client.create_authorization_url(
            AUTH_URL,
            code_challenge=code_challenge,
            code_challenge_method="S256",
            scope=SCOPE,
            state=session_id  # Incluir session_id como state para validación adicional
        )[0]

        webbrowser.open(auth_url)
        
        # 8. Esperar hasta que se complete la autorización
        timeout = 300  # 5 minutos de timeout
        wait_time = 0
        
        while not oauth_sessions[session_id]['completed'] and wait_time < timeout:
            await asyncio.sleep(1)
            wait_time += 1
        
        session_data = oauth_sessions[session_id]
        
        if wait_time >= timeout:
            # print(f"Timeout para sesión {session_id}")
            return None
            
        if session_data['error']:
            # print(f"Error en autorización para sesión {session_id}: {session_data['error']}")
            return None

        if not session_data['code']:
            # print(f"No se recibió código para sesión {session_id}")
            return None

        # 9. Intercambiar código por tokens
        token = await client.fetch_token(
            TOKEN_URL,
            code=session_data['code'],
            code_verifier=code_verifier,
        )
        
        # 10. Validación segura con verificación de firma JWT
        user_data = await validate_and_get_user_info_secure(token, CLIENT_ID)
        
        return {
            'session_id': session_id,
            'token': token,
            'user_data': user_data
        }

    except Exception as e:
        return None
    finally:
        # 11. Limpiar la sesión después de un tiempo
        async def cleanup_session():
            await asyncio.sleep(300)  # Esperar 5 minutos antes de limpiar
            if session_id in oauth_sessions:
                del oauth_sessions[session_id]
        
        asyncio.create_task(cleanup_session())

# Función wrapper para mantener compatibilidad
async def run_google_pkce_auth_secure():
    """Ejecucion de autenticación segura con PKCE."""
    result = await run_google_pkce_auth_secure_multiuser()
    if result:
        # Devolver en el formato esperado
        return {
            'token': result['token'],
            'user_data': result['user_data']
        }
    return None

if __name__ == "__main__":
    # Test de la funcionalidad
    async def test_multiuser():
        result = await run_google_pkce_auth_secure_multiuser()
        if result:
            if result['user_data'].get('jwt_validation', {}).get('signature_valid'):
                email = result['user_data']['id_token_data']['email']
                print(f"Autenticación segura completada! Usuario autenticado: {email}")
        else:
            print("Autenticación falló")
            print(result)
    
    asyncio.run(test_multiuser())