"""
Configuración y cliente Redis para el manejo de sesiones
"""
import os
import asyncio
import redis.asyncio as redis
from typing import Optional, Dict, Any
import json
from datetime import datetime, timezone
from src.tools.logger_config import LoggerSetup

class RedisConfig:
    """Configuración centralizada de Redis"""
    
    def __init__(self):
        # IMPORTANTE: Usar 'redis' como hostname cuando está en Docker
        # En desarrollo local, cambiar a 'localhost'
        self.host = os.getenv('REDIS_HOST', 'redis')  # Cambiar de 'localhost' a 'redis'
        self.port = int(os.getenv('REDIS_PORT', 6379))
        self.db = int(os.getenv('REDIS_DB', 0))
        self.password = os.getenv('REDIS_PASSWORD')
        self.decode_responses = True
        self.socket_connect_timeout = 10  # Aumentar timeout
        self.socket_timeout = 10
        self.retry_on_timeout = True
        self.max_connections = 20

class RedisClient:
    """Cliente Redis con manejo correcto de event loops"""
    
    _instance: Optional["RedisClient"] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisClient, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, "_initialized") and self._initialized:
            return
        
        self._initialized = True
        self.config = RedisConfig()
        self.logger = LoggerSetup(file_name="redis.log").create_module_logger("redis")
        self._clients: Dict[int, redis.Redis] = {}  # Un cliente por event loop
        self._pools: Dict[int, redis.ConnectionPool] = {}
    
    def _get_loop_id(self) -> int:
        """Obtiene el ID del event loop actual"""
        try:
            loop = asyncio.get_running_loop()
            return id(loop)
        except RuntimeError:
            # No hay event loop activo
            return 0
    
    async def connect(self) -> redis.Redis:
        """Establece conexión con Redis para el event loop actual"""
        loop_id = self._get_loop_id()
        
        # Si ya tenemos un cliente para este event loop, lo devolvemos
        if loop_id in self._clients:
            try:
                # Verificar que la conexión sigue activa
                await self._clients[loop_id].ping()
                return self._clients[loop_id]
            except:
                # La conexión se perdió, eliminar cliente corrupto
                if loop_id in self._clients:
                    try:
                        await self._clients[loop_id].aclose()
                    except:
                        pass
                    del self._clients[loop_id]
                
                if loop_id in self._pools:
                    try:
                        await self._pools[loop_id].aclose()
                    except:
                        pass
                    del self._pools[loop_id]
        
        # Crear nuevo cliente para este event loop
        max_retries = 5
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                self.logger.info(f"Conectando a Redis: {self.config.host}:{self.config.port} (intento {attempt + 1}/{max_retries})")
                
                # Crear connection pool específico para este event loop
                pool_config = {
                    'host': self.config.host,
                    'port': self.config.port,
                    'db': self.config.db,
                    'decode_responses': self.config.decode_responses,
                    'socket_connect_timeout': self.config.socket_connect_timeout,
                    'socket_timeout': self.config.socket_timeout,
                    'retry_on_timeout': self.config.retry_on_timeout,
                    'max_connections': self.config.max_connections,
                }
                
                if self.config.password:
                    pool_config['password'] = self.config.password
                
                # Crear pool y cliente
                pool = redis.ConnectionPool(**pool_config)
                client = redis.Redis(connection_pool=pool)
                
                # Test de conexión
                await client.ping()
                
                # Guardar cliente y pool para este event loop
                self._pools[loop_id] = pool
                self._clients[loop_id] = client
                
                self.logger.info("✅ Redis conectado exitosamente")
                return client
                
            except Exception as e:
                self.logger.warning(f"❌ Intento {attempt + 1} falló: {e}")
                
                if attempt < max_retries - 1:
                    self.logger.info(f"Reintentando en {retry_delay} segundos...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5
                else:
                    self.logger.error(f"❌ Error conectando a Redis después de {max_retries} intentos")
                    raise ConnectionError(f"No se pudo conectar a Redis: {e}")
        
        raise ConnectionError("No se pudo establecer conexión con Redis")
    
    async def disconnect(self, loop_id: Optional[int] = None):
        """Cierra la conexión con Redis para un event loop específico o todos"""
        if loop_id is None:
            loop_id = self._get_loop_id()
        
        if loop_id in self._clients:
            try:
                await self._clients[loop_id].aclose()
            except:
                pass
            del self._clients[loop_id]
        
        if loop_id in self._pools:
            try:
                await self._pools[loop_id].aclose()
            except:
                pass
            del self._pools[loop_id]
        
        self.logger.info(f"Redis desconectado para loop {loop_id}")
    
    async def disconnect_all(self):
        """Cierra todas las conexiones Redis"""
        for loop_id in list(self._clients.keys()):
            await self.disconnect(loop_id)
        self.logger.info("Todas las conexiones Redis cerradas")
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica el estado de la conexión Redis"""
        try:
            client = await self.connect()
            await client.ping()
            info = await client.info()
            
            return {
                'status': 'healthy',
                'connected': True,
                'redis_version': info.get('redis_version'),
                'used_memory': info.get('used_memory_human'),
                'connected_clients': info.get('connected_clients'),
                'total_commands_processed': info.get('total_commands_processed'),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'current_loop_id': self._get_loop_id(),
                'active_connections': len(self._clients)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e),
                'current_loop_id': self._get_loop_id(),
                'active_connections': len(self._clients)
            }

# Cliente global
redis_client = RedisClient()