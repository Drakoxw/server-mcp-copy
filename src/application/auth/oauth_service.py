"""
Servicio OAuth refactorizado usando Redis para sesiones
"""
import os
import secrets
import hashlib
import jwt
import base64
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from authlib.integrations.httpx_client import AsyncOAuth2Client
from src.application.auth.google_jwks_client import GoogleJWKSClient
from src.infrastructure.session.session_service import SessionStatus, session_service
# from src.infrastructure.session.user_session import AveSession
from src.tools.logger_config import LoggerSetup
import httpx

from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class OAuthConfig:
    """Configuración centralizada de OAuth"""
    client_id: str = os.getenv("CLIENT_ID", "")
    client_secret: str = os.getenv("CLIENT_SECRET", "")
    callback_server_port: int = int(os.getenv("CALLBACK_SERVER_PORT", 3030))
    redirect_uri: str = os.getenv("REDIRECT_URI", "http://localhost")
    auth_url: str = "https://accounts.google.com/o/oauth2/v2/auth"
    token_url: str = "https://oauth2.googleapis.com/token"
    userinfo_url: str = "https://www.googleapis.com/oauth2/v2/userinfo"
    scope: str = "openid email profile"
    session_timeout: int = 300  # 5 minutos para completar OAuth
    jwt_leeway: int = 60

@dataclass
class ValidationResult:
    valid: bool
    payload: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    validation_details: Optional[Dict[str, Any]] = None

@dataclass
class UserData:
    id_token_data: Optional[Dict[str, Any]] = None
    api_data: Optional[Dict[str, Any]] = None
    jwt_validation: Optional[Dict[str, Any]] = None
    token_validation: Optional[Dict[str, Any]] = None
    api_error: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class OAuthService:
    """Servicio OAuth usando Redis para gestión de sesiones"""

    _instance: Optional["OAuthService"] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(OAuthService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        self._initialized = True

        self.config = OAuthConfig()
        self.jwks_client = GoogleJWKSClient()
        self.logger = LoggerSetup(file_name="oauth-service.log").create_module_logger("oauth")
        self._http_client: Optional[httpx.AsyncClient] = None

        self._validate_config()
    
    def _validate_config(self):
        """Valida la configuración necesaria"""
        if not self.config.client_id or not self.config.client_secret:
            raise ValueError("CLIENT_ID y CLIENT_SECRET son requeridos")
    
    def _generate_code_verifier(self) -> str:
        """Genera un code_verifier válido según RFC 7636"""
        random_bytes = secrets.token_bytes(32)
        code_verifier = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')
        
        if len(code_verifier) < 43:
            random_bytes = secrets.token_bytes(43)
            code_verifier = base64.urlsafe_b64encode(random_bytes).decode('utf-8').rstrip('=')
        
        if len(code_verifier) > 128:
            code_verifier = code_verifier[:128]
            
        return code_verifier
    
    def _create_s256_code_challenge(self, code_verifier: str) -> str:
        """Crea el code_challenge usando SHA256 y base64url según RFC 7636"""
        digest = hashlib.sha256(code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(digest).decode('utf-8').rstrip('=')
        return code_challenge
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Cliente HTTP reutilizable con configuración optimizada"""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
            )
        return self._http_client
    
    async def create_oauth_url(self) -> Dict[str, str]:
        """Crea la URL de autorización para el flujo OAuth con PKCE"""
        try:
            # Generar code_verifier y code_challenge
            code_verifier = self._generate_code_verifier()
            code_challenge = self._create_s256_code_challenge(code_verifier)
            
            # Datos de la sesión
            session_data = {
                'code_verifier': code_verifier,
                'redirect_uri': f"{self.config.redirect_uri}:{self.config.callback_server_port}/callback",
                'created_for': 'oauth_flow'
            }
            
            # Crear sesión en Redis
            session_id = await session_service.create_session(
                session_data, 
                ttl=self.config.session_timeout
            )
            
            # Configurar redirect URI con session_id
            redirect_uri = f"{self.config.redirect_uri}:{self.config.callback_server_port}/callback/{session_id}"
            
            # Actualizar redirect_uri en la sesión
            await session_service.update_session(session_id, {'redirect_uri': redirect_uri})
            
            # Crear cliente OAuth2 con PKCE
            client = AsyncOAuth2Client(
                client_id=self.config.client_id,
                client_secret=self.config.client_secret,
                redirect_uri=redirect_uri
            )
            
            auth_url, state = client.create_authorization_url(
                self.config.auth_url,
                code_challenge=code_challenge,
                code_challenge_method="S256",
                scope=self.config.scope,
                state=session_id,
                access_type="offline",
                prompt="consent"
            )
            
            self.logger.info(f"URL OAuth creada para sesión: {session_id}")
            
            return {
                "auth_url": auth_url,
                "session_id": session_id
            }
            
        except Exception as e:
            self.logger.error(f"Error creando URL OAuth: {e}")
            raise
    
    async def handle_oauth_callback(self, session_id: str, code: Optional[str] = None, error: Optional[str] = None) -> bool:
        """Maneja el callback de OAuth y actualiza la sesión"""
        try:
            if error:
                await session_service.update_session_status(session_id, SessionStatus.ERROR, error=error)
                return False
            
            if code:
                await session_service.update_session_status(session_id, SessionStatus.COMPLETED, code=code)
                return True
            
            await session_service.update_session_status(session_id, SessionStatus.ERROR, error="No code received")
            return False
            
        except Exception as e:
            self.logger.error(f"Error manejando callback OAuth: {e}")
            await session_service.update_session_status(session_id, SessionStatus.ERROR, error=str(e))
            return False
    
    async def verify_oauth_session(self, session_id: str) -> Dict[str, Any]:
        """Verifica y procesa una sesión OAuth completa"""
        try:
            # Verificar que la sesión existe
            session_data = await session_service.get_session(session_id)
            if not session_data:
                raise ValueError(f"Sesión {session_id} no existe o ha expirado")
            
            # Esperar a que se complete la autorización
            wait_time = 0
            max_wait = self.config.session_timeout
            
            while session_data.get('status') == SessionStatus.PENDING.value and wait_time < max_wait:
                await asyncio.sleep(1)
                wait_time += 1
                session_data = await session_service.get_session(session_id)
                
                if not session_data:
                    raise ValueError("Sesión expiró durante la autorización")
            
            if wait_time >= max_wait:
                await session_service.update_session_status(session_id, SessionStatus.EXPIRED)
                raise ValueError("Timeout esperando autorización")
            
            if session_data.get('status') == SessionStatus.ERROR.value:
                error = session_data.get('error', 'Error desconocido')
                raise ValueError(f"Error en autorización: {error}")
            
            if session_data.get('status') != SessionStatus.COMPLETED.value:
                raise ValueError("Sesión no completada")
            
            code = session_data.get('code')
            if not code:
                raise ValueError("No se recibió código de autorización")
            
            # Intercambiar código por tokens
            token = await self._exchange_code_for_tokens(session_data, code)
            
            # Validar y obtener información del usuario
            user_data = await self.validate_and_get_user_info_secure(token)
            
            return {
                'session_id': session_id,
                'token': token,
                'user_data': user_data.__dict__
            }
            
        except Exception as e:
            self.logger.error(f"Error verificando sesión OAuth {session_id}: {str(e)}")
            return {
                'error': True,
                'message': str(e)
            }
    
    async def _exchange_code_for_tokens(self, session_data: Dict[str, Any], code: str) -> Dict[str, Any]:
        """Intercambia el código de autorización por tokens"""
        redirect_uri = session_data.get('redirect_uri')
        code_verifier = session_data.get('code_verifier')
        
        if not redirect_uri or not code_verifier:
            raise ValueError("Datos de sesión incompletos")
        
        client = AsyncOAuth2Client(
            client_id=self.config.client_id,
            client_secret=self.config.client_secret,
            redirect_uri=redirect_uri
        )
        
        token = await client.fetch_token(
            self.config.token_url,
            code=code,
            code_verifier=code_verifier,
        )
        
        return token
    
    
    async def _validate_jwt_signature(self, id_token: str) -> ValidationResult:
        """Valida la firma del JWT ID Token usando las claves públicas de Google"""
        try:
            # Decodificar header para obtener kid
            header = jwt.get_unverified_header(id_token)
            kid = header.get('kid')
            
            if not kid:
                return ValidationResult(
                    valid=False,
                    error='Token JWT no contiene Key ID (kid) en el header'
                )
            
            # Obtener claves públicas de Google
            jwks = await self.jwks_client.get_jwks()
            if not jwks:
                return ValidationResult(
                    valid=False,
                    error='No se pudieron obtener las claves públicas de Google'
                )
            
            key_data = self.jwks_client.get_key_by_kid(jwks, kid)
            if not key_data:
                return ValidationResult(
                    valid=False,
                    error=f'No se encontró la clave pública para kid: {kid}'
                )
            
            # Validar firma con tolerancia de tiempo
            public_key = jwt.PyJWK(key_data).key
            
            payload = jwt.decode(
                id_token,
                public_key,
                algorithms=['RS256'],
                audience=self.config.client_id,
                issuer='https://accounts.google.com',
                leeway=self.config.jwt_leeway,
                options={
                    'verify_exp': True,
                    'verify_aud': True,
                    'verify_iss': True,
                    'verify_iat': True,
                }
            )
            
            return ValidationResult(
                valid=True,
                payload=payload,
                validation_details={
                    'algorithm': header.get('alg'),
                    'key_id': kid,
                    'issuer': payload.get('iss'),
                    'audience': payload.get('aud'),
                    'subject': payload.get('sub'),
                    'issued_at': datetime.fromtimestamp(payload.get('iat', 0)),
                    'expires_at': datetime.fromtimestamp(payload.get('exp', 0)),
                    'email_verified': payload.get('email_verified', False),
                    'leeway_applied': True,
                    'leeway_seconds': self.config.jwt_leeway
                }
            )
            
        except jwt.ExpiredSignatureError:
            return ValidationResult(valid=False, error='Token JWT ha expirado')
        except jwt.InvalidAudienceError:
            return ValidationResult(valid=False, error='Audiencia del token JWT inválida')
        except jwt.InvalidIssuerError:
            return ValidationResult(valid=False, error='Emisor del token JWT inválido')
        except jwt.InvalidSignatureError:
            return ValidationResult(valid=False, error='Firma del token JWT inválida')
        except jwt.ImmatureSignatureError:
            return ValidationResult(valid=False, error='Token emitido en el futuro - sincronizar relojes del servidor')
        except jwt.InvalidIssuedAtError:
            return ValidationResult(valid=False, error='Timestamp iat (issued at) inválido en el token')
        except Exception as e:
            return ValidationResult(valid=False, error=f'Error validando JWT: {str(e)}')
    
    
    async def validate_and_get_user_info_secure(self, token: Dict[str, Any]) -> UserData:
        """Versión segura que valida la firma JWT antes de usar los datos"""
        user_data = UserData()
        
        try:
            # Validación del ID Token
            if 'id_token' in token:
                jwt_validation = await self._validate_jwt_signature(token['id_token'])
                
                if jwt_validation.valid and jwt_validation.payload is not None:
                    # CORRECCIÓN: Verificar que payload no es None antes de usar .get()
                    payload = jwt_validation.payload
                    user_data.id_token_data = {
                        'user_id': payload.get('sub'),
                        'email': payload.get('email'),
                        'email_verified': payload.get('email_verified'),
                        'name': payload.get('name'),
                        'picture': payload.get('picture'),
                        'given_name': payload.get('given_name'),
                        'family_name': payload.get('family_name'),
                        'locale': payload.get('locale'),
                        'audience': payload.get('aud'),
                        'issuer': payload.get('iss'),
                    }
                    
                    # CORRECCIÓN: Verificar que validation_details no es None antes de acceder
                    if jwt_validation.validation_details is not None:
                        user_data.id_token_data.update({
                            'issued_at': jwt_validation.validation_details.get('issued_at'),
                            'expires_at': jwt_validation.validation_details.get('expires_at'),
                        })
                        
                        # CORRECCIÓN: Usar copy() o dict() para evitar problemas con el operador **
                        user_data.jwt_validation = dict(jwt_validation.validation_details)
                        user_data.jwt_validation['signature_valid'] = True
                    else:
                        # Si validation_details es None, crear un diccionario básico
                        user_data.jwt_validation = {
                            'signature_valid': True,
                            'payload_extracted': True
                        }
                else:
                    user_data.jwt_validation = {
                        'signature_valid': False,
                        'error': jwt_validation.error
                    }
            
            # Obtener información del usuario desde la API
            if 'access_token' in token:
                api_data, api_error = await self._get_user_info_from_api(token['access_token'])
                user_data.api_data = api_data
                user_data.api_error = api_error
                
                # Validar access token
                user_data.token_validation = await self._validate_access_token(token['access_token'])
            
            return user_data
            
        except Exception as e:
            user_data.error = str(e)
            return user_data
    
    
    
    async def _validate_access_token(self, access_token: str) -> Dict[str, Any]:
        """Valida el access token con la API de Google"""
        try:
            client = await self._get_http_client()
            validate_url = f"https://oauth2.googleapis.com/tokeninfo?access_token={access_token}"
            response = await client.get(validate_url)
            
            if response.status_code == 200:
                token_info = response.json()
                return {
                    'valid': True,
                    'scope': token_info.get('scope'),
                    'audience': token_info.get('aud'),
                    'expires_in': token_info.get('expires_in'),
                }
            else:
                return {
                    'valid': False,
                    'error': response.text
                }
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error validando access token: {str(e)}'
            }
    
    async def _get_user_info_from_api(self, access_token: str) -> Tuple[Optional[Dict], Optional[Dict]]:
        """Obtiene información del usuario desde la API de Google"""
        try:
            client = await self._get_http_client()
            headers = {'Authorization': f"Bearer {access_token}"}
            response = await client.get(self.config.userinfo_url, headers=headers)
            
            if response.status_code == 200:
                return response.json(), None
            else:
                return None, {
                    'status_code': response.status_code,
                    'error': response.text
                }
        except Exception as e:
            return None, {'error': str(e)}

    
    async def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene información de una sesión específica"""
        return await session_service.get_session(session_id)
    
    async def get_all_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene todas las sesiones OAuth activas"""
        return await session_service.get_all_active_sessions()
    
    async def cleanup_expired_sessions(self) -> int:
        """Limpia sesiones expiradas"""
        return await session_service.cleanup_expired_sessions()
    
    async def cleanup_resources(self):
        """Limpia recursos y cierra conexiones"""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
        
        self.logger.info("Recursos de OAuth limpiados")

# Instancia global optimizada
oauth_service_global = OAuthService()

# # Funciones de compatibilidad con la API anterior
# async def validate_jwt_signature(id_token, client_id):
#     """Función de compatibilidad - usar oauth_service._validate_jwt_signature"""
#     result = await oauth_service._validate_jwt_signature(id_token)
#     return asdict(result)

# async def validate_and_get_user_info_secure(token, client_id):
#     """Función de compatibilidad"""
#     result = await oauth_service.validate_and_get_user_info_secure(token)
#     return asdict(result)

def create_oauth_url():
    """Función de compatibilidad"""
    return oauth_service_global.create_oauth_url()

# async def verify_oauth_session(session_id: str, code_verifier: str = ""):
#     """Función de compatibilidad"""
#     return await oauth_service.verify_oauth_session(session_id)

# def get_oauth_sessions(session_id: str):
#     """Función de compatibilidad"""
#     return oauth_service.get_session_info(session_id)

# def get_all_oauth_sessions():
#     """Función de compatibilidad"""
#     return session_service.get_all_active_sessions()