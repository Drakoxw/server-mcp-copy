"""
Servidor FastAPI optimizado para callbacks OAuth con Google
"""
from datetime import datetime, timezone
import os
import asyncio
import logging
from threading import Thread, Event
from typing import Optional, Dict, Any

from dotenv import load_dotenv

from src.tools.base.common import validate_email
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import HTMLResponse
import uvicorn
from dataclasses import asdict


from src.application.auth.ave_online_auth import AveOnlineAuth
from src.application.auth.oauth_service import oauth_service_global
from src.infrastructure.session.session_service import SessionStatus, session_service

# Configuración
CALLBACK_SERVER_PORT = int(os.getenv("CALLBACK_SERVER_PORT", 3030))
CALLBACK_SERVER_HOST = os.getenv("CALLBACK_SERVER_HOST", "0.0.0.0")
LOG_LEVEL = os.getenv("LOG_LEVEL", "info").lower()

# Logger configurado
logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper()))
logger = logging.getLogger(__name__)

class OptimizedCallbackServer:
    """Servidor optimizado para callbacks OAuth"""
    
    def __init__(self):
        self.session_service = session_service
        self.oauth_service = oauth_service_global
        self.server_thread: Optional[Thread] = None
        self.server_stop_event = Event()
        self.app = self._create_app()
        self.ave_session = AveOnlineAuth()
        
    def _create_app(self) -> FastAPI:
        """Crea la aplicación FastAPI con configuración optimizada"""
        
        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Manejo del ciclo de vida de la aplicación"""
            logger.info("Iniciando servidor de callbacks OAuth")
            yield
            logger.info("Cerrando servidor de callbacks OAuth")
            # await self.oauth_service.cleanup_resources()
            await self.session_service.cleanup_expired_sessions()
        
        app = FastAPI(
            title="OAuth Callback Server Optimizado",
            description="Servidor para manejar callbacks de autenticación OAuth con Google",
            version="2.0.0",
            lifespan=lifespan,
            docs_url="/docs" if LOG_LEVEL == "debug" else None,
            redoc_url="/redoc" if LOG_LEVEL == "debug" else None
        )
        
        # # Middleware de seguridad
        # app.add_middleware(
        #     TrustedHostMiddleware,
        #     allowed_hosts=[CALLBACK_SERVER_HOST, "127.0.0.1", "localhost", f"127.0.0.1:{CALLBACK_SERVER_PORT}"]
        # )
        
        # CORS para desarrollo local
        # app.add_middleware(
        #     CORSMiddleware,
        #     allow_origins=[f"http://{CALLBACK_SERVER_HOST}:{CALLBACK_SERVER_PORT}", f"http://127.0.0.1:{CALLBACK_SERVER_PORT}", f"http://localhost:{CALLBACK_SERVER_PORT}"],
        #     allow_credentials=True,
        #     allow_methods=["GET"],
        #     allow_headers=["*"],
        # )
        
        # Registrar rutas
        self._register_routes(app)
        
        return app
    
    def _register_routes(self, app: FastAPI):
        """Registra todas las rutas del servidor"""

        @app.get("/callback/{session_id}", response_class=HTMLResponse)
        async def oauth_callback(
            request: Request,
            session_id: str, 
            code: Optional[str] = Query(None, description="Código de autorización de Google"), 
            error: Optional[str] = Query(None, description="Error de autorización"),
            state: Optional[str] = Query(None, description="Estado de la sesión"),
            scope: Optional[str] = Query(None, description="Scopes autorizados")
        ):
            """Endpoint optimizado para manejar callbacks de OAuth por sesión"""
            try:
                logger.info(f"Callback recibido para sesión {session_id}")
                # Actualizar la sesión con el código
                await self.session_service.update_session_status(session_id, status=SessionStatus.UPDATED)

                # Validar que la sesión existe
                session_data = self.session_service.get_session(session_id)

                if not session_data:
                    raise HTTPException(status_code=404, detail="Sesión no encontrada o expirada")

                # Validar el state parameter contra el session_id
                if state and state != session_id:
                    await self.session_service.update_session_status(session_id=session_id, status=SessionStatus.ERROR, error="State parameter mismatch")
                    return self._error_response("Error de validación de estado")

                # Manejar errores de autorización
                if error:
                    await self.session_service.update_session_status(session_id, status=SessionStatus.ERROR, error=error)
                    return self._error_response(f"Error de autorización: {error}")

                # Validar que se recibió el código
                if not code:
                    await self.session_service.update_session_status(session_id, status=SessionStatus.ERROR, error="No se recibió código de autorización")
                    return self._error_response("No se recibió código de autorización")


                # Actualizar la sesión con el código
                await self.session_service.update_session_status(session_id, status=SessionStatus.COMPLETED, code=code)

                # ⚠️ Esperar a que el flujo se complete y obtener los datos del usuario
                result = await self.oauth_service.verify_oauth_session(session_id)

                if "error" in result:
                    return self._error_response(f"Error autenticando al usuario: {result['message']}")

                # ✅ Usuario autenticado correctamente
                user_info = result.get("user_data", {}).get("id_token_data", {})
                email = user_info.get("email", "email no disponible")

                if validate_email(email) == False:
                    return self._error_response("No se recibió un correo valido")

                session = await self.ave_session.loginOAuth(email)

                if session.get("error"):
                    ### No se encontro el usuario -> llevar al flujo de registro
                    return self._error_response(f"Error iniciando sesión en AveOnline: {session.get('message')}")

                await self.session_service.update_session(
                    session_id, 
                    updates={"ave_session" : asdict(session["data"])},
                    extend_ttl=True
                )

                return self._success_response()

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error procesando callback para sesión {session_id}: {str(e)}")
                return self._error_response("Error interno del servidor")
        
        @app.get("/sessions", response_model=Dict[str, Any])
        async def get_sessions_status():
            """Endpoint para monitorear sesiones activas (solo en debug)"""
            
            if LOG_LEVEL != "debug":
                raise HTTPException(status_code=404, detail="Endpoint no disponible")
            
            try:
                oauth_sessions = await self.oauth_service.get_all_active_sessions()
                
                return {
                    "timestamp": asyncio.get_event_loop().time(),
                    "active_sessions": len(oauth_sessions),
                    "date_time": datetime.now(timezone.utc).isoformat(),
                    "sessions": {
                        session_id: {
                            "status": data.get("status", "unknown"),
                            "has_code": data.get("code") is not None,
                            "has_error": data.get("error") is not None,
                            "created_at": data.get("created_at"),
                            "expires_at": data.get("expires_at"),
                            "is_expired": data.get("is_expired", False),
                            "ave_id": data.get("ave_session", {}).get("idEnterprise", None)
                        }
                        for session_id, data in oauth_sessions.items()
                    }
                }
                
            except Exception as e:
                logger.error(f"Error obteniendo sesiones: {str(e)}")
                raise HTTPException(status_code=500, detail="Error interno")
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "server": "oauth-callback",
                "version": "2.0.0"
            }
        
        @app.exception_handler(404)
        async def not_found_handler(request: Request, exc: HTTPException):
            """Manejador personalizado para 404"""
            return self._error_response("Página no encontrada")
        
        @app.exception_handler(500)
        async def internal_error_handler(request: Request, exc: Exception):
            """Manejador personalizado para errores internos"""
            logger.error(f"Error interno: {str(exc)}")
            return self._error_response("Error interno del servidor")
    
    def _success_response(self) -> HTMLResponse:
        """Respuesta HTML optimizada para autorización exitosa"""
        return HTMLResponse("""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Autorización Exitosa</title>
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex; 
                    justify-content: center; 
                    align-items: center; 
                    height: 100vh; 
                    margin: 0; 
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .container { 
                    text-align: center; 
                    padding: 2rem;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                }
                h1 { margin-bottom: 1rem; font-size: 2rem; }
                p { margin-bottom: 1.5rem; opacity: 0.9; }
                .spinner {
                    width: 20px; height: 20px;
                    border: 2px solid rgba(255,255,255,0.3);
                    border-top: 2px solid white;
                    border-radius: 50%;
                    animation: spin 1s linear infinite;
                    display: inline-block;
                    margin-right: 10px;
                }
                @keyframes spin { to { transform: rotate(360deg); } }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✅ ¡Autorización exitosa!</h1>
                <p>Tu cuenta ha sido autenticada correctamente.</p>
                <p><span class="spinner"></span>Cerrando ventana automáticamente...</p>
            </div>
            <script>
                // Cerrar ventana automáticamente después de 3 segundos
                setTimeout(() => {
                    try {
                        window.close();
                    } catch(e) {
                        // Si no se puede cerrar, mostrar mensaje
                        document.querySelector('.container').innerHTML = 
                            '<h1>✅ Autorización exitosa</h1><p>Puedes cerrar esta ventana manualmente.</p>';
                    }
                }, 3000);
                
                // Intentar enviar mensaje al padre si está en iframe
                try {
                    if (window.parent && window.parent !== window) {
                        window.parent.postMessage({type: 'oauth_success'}, '*');
                    }
                } catch(e) {
                    console.log('No se pudo comunicar con ventana padre');
                }
            </script>
        </body>
        </html>
        """)
    
    def _error_response(self, error_message: str) -> HTMLResponse:
        """Respuesta HTML optimizada para errores"""
        return HTMLResponse(f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Error de Autorización</title>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex; 
                    justify-content: center; 
                    align-items: center; 
                    height: 100vh; 
                    margin: 0; 
                    background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);
                    color: white;
                }}
                .container {{ 
                    text-align: center; 
                    padding: 2rem;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                    max-width: 500px;
                }}
                h1 {{ margin-bottom: 1rem; font-size: 2rem; }}
                .error {{ 
                    background: rgba(255, 255, 255, 0.2);
                    padding: 1rem;
                    border-radius: 8px;
                    margin: 1rem 0;
                    word-break: break-word;
                }}
                button {{
                    background: rgba(255, 255, 255, 0.2);
                    border: none;
                    padding: 0.5rem 1rem;
                    border-radius: 5px;
                    color: white;
                    cursor: pointer;
                    margin-top: 1rem;
                }}
                button:hover {{ background: rgba(255, 255, 255, 0.3); }}
            }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>❌ Error de Autorización</h1>
                <div class="error">
                    <strong>Error:</strong> {error_message}
                </div>
                <p>Por favor, intenta nuevamente o contacta al administrador.</p>
                <button onclick="window.close()">Cerrar Ventana</button>
            </div>
            <script>
                // Enviar mensaje de error al padre si está disponible
                try {{
                    if (window.parent && window.parent !== window) {{
                        window.parent.postMessage({{
                            type: 'oauth_error', 
                            error: '{error_message}'
                        }}, '*');
                    }}
                }} catch(e) {{
                    console.log('No se pudo comunicar con ventana padre');
                }}
            </script>
        </body>
        </html>
        """)
    
    def start_server(self, background: bool = True) -> bool:
        """Inicia el servidor de callbacks"""
        
        if self.server_thread and self.server_thread.is_alive():
            logger.warning("El servidor ya está ejecutándose")
            return True
        
        try:
            if background:
                self.server_thread = Thread(
                    target=self._run_server_thread,
                    name="OAuth-Callback-Server",
                    daemon=True
                )
                self.server_thread.start()
                
                # Esperar un poco para verificar que se inició correctamente
                import time
                time.sleep(1.5)
                
                if self.server_thread.is_alive():
                    logger.info(f"Servidor de callbacks iniciado en http://{CALLBACK_SERVER_HOST}:{CALLBACK_SERVER_PORT}")
                    return True
                else:
                    logger.error("Error iniciando el servidor de callbacks")
                    return False
            else:
                # Modo síncrono para testing
                self._run_server_thread()
                return True
                
        except Exception as e:
            logger.error(f"Error iniciando servidor: {str(e)}")
            return False
    
    def _run_server_thread(self):
        """Ejecuta el servidor en un hilo separado"""
        try:
            config = uvicorn.Config(
                app=self.app,
                host=CALLBACK_SERVER_HOST,
                port=CALLBACK_SERVER_PORT,
                log_level=LOG_LEVEL,
                access_log=LOG_LEVEL == "debug",
                reload=True,
                loop="asyncio"
            )
            
            server = uvicorn.Server(config)
            
            # NO configurar signal handlers en hilos secundarios
            # El control se maneja via server_stop_event
            
            # Ejecutar servidor con manejo de eventos
            asyncio.run(self._run_server_with_shutdown(server))
            
        except Exception as e:
            logger.error(f"Error en servidor: {str(e)}")
            self.server_stop_event.set()
    
    async def _run_server_with_shutdown(self, server):
        """Ejecuta el servidor con manejo de shutdown controlado"""
        try:
            # Crear task para el servidor
            server_task = asyncio.create_task(server.serve())
            
            # Crear task para monitorear el evento de parada
            async def wait_for_shutdown():
                while not self.server_stop_event.is_set():
                    await asyncio.sleep(0.1)
                logger.info("Evento de parada detectado, cerrando servidor...")
                server.should_exit = True
            
            shutdown_task = asyncio.create_task(wait_for_shutdown())
            
            # Ejecutar ambos tasks y esperar a que uno termine
            done, pending = await asyncio.wait(
                [server_task, shutdown_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Cancelar tasks pendientes
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            logger.info("Servidor OAuth detenido correctamente")
            
        except Exception as e:
            logger.error(f"Error ejecutando servidor: {str(e)}")
            raise
    
    def stop_server(self):
        """Detiene el servidor de callbacks"""
        try:
            logger.info("Iniciando shutdown del servidor OAuth...")
            self.server_stop_event.set()
            
            if self.server_thread and self.server_thread.is_alive():
                logger.info("Esperando que termine el hilo del servidor...")
                self.server_thread.join(timeout=10)  # Aumentar timeout
                
                if self.server_thread.is_alive():
                    logger.warning("El servidor no se detuvo en el tiempo esperado")
                else:
                    logger.info("Servidor de callbacks detenido correctamente")
            else:
                logger.info("El servidor no estaba ejecutándose")
                
        except Exception as e:
            logger.error(f"Error deteniendo servidor: {str(e)}")
    
    def is_running(self) -> bool:
        """Verifica si el servidor está ejecutándose"""
        return (
            self.server_thread is not None and 
            self.server_thread.is_alive() and 
            not self.server_stop_event.is_set()
        )

# Instancia global optimizada
callback_server_instance = OptimizedCallbackServer()

# Funciones de compatibilidad con la API anterior
def start_callback_server():
    """Función de compatibilidad - usar callback_server_instance.start_server()"""
    return callback_server_instance.start_server()

def stop_callback_server():
    """Nueva función para detener el servidor limpiamente"""
    return callback_server_instance.stop_server()

def is_callback_server_running():
    """Nueva función para verificar estado del servidor"""
    return callback_server_instance.is_running()

# Para uso directo del módulo
if __name__ == "__main__":
    # Configurar logging para ejecución directa
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    server = OptimizedCallbackServer()
    
    try:
        logger.info("Iniciando servidor de callbacks OAuth...")
        # En modo directo, usar el hilo principal para signal handlers
        server.start_server(background=False)
    except KeyboardInterrupt:
        logger.info("Deteniendo servidor...")
        server.stop_server()
    except Exception as e:
        logger.error(f"Error: {e}")
        server.stop_server()