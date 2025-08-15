"""
Servicio para gestión de sesiones OAuth con Redis (VERSIÓN CORREGIDA)
"""
import json
import os
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, Any
from dataclasses import asdict
from enum import Enum

from src.infrastructure.config.common_config import CommonConfig
from src.infrastructure.config.redis_config import redis_client
from src.tools.logger_config import LoggerSetup

TTL_SUCCESS = int(CommonConfig.TOKEN_LIFE_TIME_HOURS.value) * 3600

class SessionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"
    EXPIRED = "expired"
    UPDATED = "updating"
    AVE_SESSION = "successful"  # Corregido: "succesfull" -> "successful"

class AveSessionEncoder(json.JSONEncoder):
    """Encoder personalizado para objetos AveSession"""
    def default(self, obj):
        # Si el objeto tiene un método to_dict, lo usa
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        # Si es un dataclass, usa asdict
        if hasattr(obj, '__dataclass_fields__'):
            return asdict(obj)
        # Si tiene __dict__, lo convierte a diccionario
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return super().default(obj)

class SessionService:
    """Servicio para gestión de sesiones OAuth usando Redis"""
    
    def __init__(self):
        self.redis = redis_client
        self.logger = LoggerSetup(file_name="session-service.log").create_module_logger("session")
        self.session_prefix = "ave:session:"
        self.default_ttl = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hora
        
    def _get_session_key(self, session_id: str) -> str:
        """Genera la clave Redis para una sesión"""
        return f"{self.session_prefix}{session_id}"
    
    def _serialize_data(self, data: Dict[str, Any]) -> str:
        """Serializa datos usando el encoder personalizado"""
        try:
            return json.dumps(data, cls=AveSessionEncoder, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error serializando datos: {e}")
            # Fallback: intentar serializar solo los campos básicos
            basic_data = {}
            for key, value in data.items():
                try:
                    json.dumps(value)  # Test si es serializable
                    basic_data[key] = value
                except (TypeError, ValueError):
                    # Si no es serializable, convertir a string
                    basic_data[key] = str(value)
            return json.dumps(basic_data, ensure_ascii=False)
    
    async def create_session(self, session_data: Dict[str, Any], ttl: Optional[int] = None) -> str:
        """Crea una nueva sesión OAuth en Redis"""
        try:
            client = await self.redis.connect()
            session_id = str(uuid.uuid4())
            session_key = self._get_session_key(session_id)
            
            time_expire = ttl or self.default_ttl
            now = datetime.now(timezone.utc)
            expires_at = now + timedelta(seconds=time_expire)  # CORREGIDO: usar seconds en lugar de pasar entero
            
            # Agregar metadatos de sesión
            enhanced_data = {
                **session_data,
                'session_id': session_id,
                'status': SessionStatus.PENDING.value,
                'created_at': now.isoformat(),
                'expires_at': expires_at.isoformat(),
                'ttl': time_expire
            }
            
            # Serializar con encoder personalizado
            serialized_data = self._serialize_data(enhanced_data)
            
            # Guardar en Redis con TTL
            await client.setex(
                session_key,
                time_expire,
                serialized_data
            )
            
            self.logger.info(f"Sesión creada: {session_id} (TTL: {time_expire}s, expira: {expires_at})")
            return session_id
            
        except Exception as e:
            self.logger.error(f"Error creando sesión: {e}")
            raise
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene una sesión específica de Redis"""
        try:
            client = await self.redis.connect()
            session_key = self._get_session_key(session_id)
            
            session_data = await client.get(session_key)
            if session_data:
                data = json.loads(session_data)
                
                # Verificar expiración manual (Redis ya debería haber eliminado, pero por seguridad)
                if 'expires_at' in data:
                    expires_at = datetime.fromisoformat(data['expires_at'])
                    if datetime.now(timezone.utc) > expires_at:
                        self.logger.warning(f"Sesión {session_id} expirada manualmente")
                        await self.delete_session(session_id)
                        return None
                
                return data
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo sesión {session_id}: {e}")
            return None
    
    async def update_session(self, session_id: str, updates: Dict[str, Any], extend_ttl: bool = False) -> bool:
        """Actualiza una sesión existente"""
        try:
            client = await self.redis.connect()
            session_key = self._get_session_key(session_id)
            
            # Obtener datos actuales
            current_data = await self.get_session(session_id)
            if not current_data:
                self.logger.warning(f"Sesión {session_id} no encontrada para actualizar")
                return False

            self.logger.info(f"✅✅✅ Actualizando sesión {session_id}")
            
            # Convertir objetos complejos en updates si es necesario
            processed_updates = {}
            for key, value in updates.items():
                try:
                    # Test si es serializable directamente
                    json.dumps(value)
                    processed_updates[key] = value
                except (TypeError, ValueError):
                    # Si no es serializable, usar el encoder personalizado
                    if hasattr(value, 'to_dict'):
                        processed_updates[key] = value.to_dict()
                    elif hasattr(value, '__dataclass_fields__'):
                        processed_updates[key] = asdict(value)
                    elif hasattr(value, '__dict__'):
                        processed_updates[key] = value.__dict__
                    else:
                        processed_updates[key] = str(value)
            
            # Aplicar actualizaciones
            updated_data = {**current_data, **processed_updates}
            updated_data['updated_at'] = datetime.now(timezone.utc).isoformat()
            
            # Actualizar tiempo de expiración si se extiende TTL
            if extend_ttl:
                new_expires_at = datetime.now(timezone.utc) + timedelta(seconds=TTL_SUCCESS)
                updated_data['expires_at'] = new_expires_at.isoformat()
                updated_data['ttl'] = TTL_SUCCESS
            
            # Serializar datos actualizados
            serialized_data = self._serialize_data(updated_data)
            
            # Guardar cambios
            await client.set(session_key, serialized_data)
            
            # Extender TTL si se solicita (cuando se crea la sesion en Ave)
            if extend_ttl:
                await client.expire(session_key, TTL_SUCCESS)
                self.logger.info(f"TTL extendido para sesión {session_id}: {TTL_SUCCESS}s")
            
            self.logger.info(f"Sesión actualizada: {session_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error actualizando sesión {session_id}: {e}")
            return False
    
    async def update_session_status(self, session_id: str, status: SessionStatus, 
                                  code: Optional[str] = None, error: Optional[str] = None) -> bool:
        """Actualiza el estado de una sesión"""
        updates = {'status': status.value}
        
        if code:
            updates['code'] = code
        if error:
            updates['error'] = error
        
        return await self.update_session(session_id, updates, extend_ttl=False)
    
    async def delete_session(self, session_id: str) -> bool:
        """Elimina una sesión de Redis"""
        try:
            client = await self.redis.connect()
            session_key = self._get_session_key(session_id)
            
            result = await client.delete(session_key)
            
            if result:
                self.logger.info(f"⚠️⚠️⚠️ Sesión eliminada: {session_id} ⚠️⚠️⚠️")
            
            return bool(result)
            
        except Exception as e:
            self.logger.error(f"Error eliminando sesión {session_id}: {e}")
            return False
    
    async def get_session_ttl(self, session_id: str) -> Optional[int]:
        """Obtiene el TTL restante de una sesión"""
        try:
            client = await self.redis.connect()
            session_key = self._get_session_key(session_id)
            
            ttl = await client.ttl(session_key)
            
            if ttl == -1:
                self.logger.warning(f"Sesión {session_id} no tiene TTL definido")
            elif ttl == -2:
                self.logger.warning(f"Sesión {session_id} no existe")
                return None
            
            return ttl if ttl > 0 else None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo TTL de sesión {session_id}: {e}")
            return None
    
    async def cleanup_expired_sessions(self) -> int:
        """Limpia sesiones expiradas manualmente"""
        try:
            client = await self.redis.connect()
            pattern = f"{self.session_prefix}*"
            
            cursor = 0
            cleaned = 0
            
            while True:
                cursor, keys = await client.scan(cursor, match=pattern, count=100)
                
                for key in keys:
                    try:
                        # Verificar si la clave aún existe (puede haber expirado durante el scan)
                        exists = await client.exists(key)
                        if not exists:
                            cleaned += 1
                            continue
                        
                        session_data = await client.get(key)
                        if session_data:
                            data = json.loads(session_data)
                            
                            if 'expires_at' in data:
                                expires_at = datetime.fromisoformat(data['expires_at'])
                                
                                if datetime.now(timezone.utc) > expires_at:
                                    await client.delete(key)
                                    cleaned += 1
                        else:
                            # Clave sin datos válidos
                            await client.delete(key)
                            cleaned += 1
                            
                    except Exception as key_error:
                        # Si hay error parseando, eliminar la clave corrupta
                        self.logger.warning(f"Clave corrupta eliminada: {key} - Error: {key_error}")
                        await client.delete(key)
                        cleaned += 1
                
                if cursor == 0:
                    break
            
            if cleaned > 0:
                self.logger.info(f"⚠️⚠️ Limpiadas {cleaned} sesiones expiradas/corruptas ⚠️⚠️")
            
            return cleaned
            
        except Exception as e:
            self.logger.error(f"Error limpiando sesiones expiradas: {e}")
            return 0
    
    async def get_all_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene todas las sesiones activas"""
        try:
            client = await self.redis.connect()
            pattern = f"{self.session_prefix}*"
            
            cursor = 0
            sessions = {}
            
            while True:
                cursor, keys = await client.scan(cursor, match=pattern, count=100)
                
                for key in keys:
                    try:
                        session_data = await client.get(key)
                        if session_data:
                            data = json.loads(session_data)
                            session_id = data.get('session_id')
                            
                            if session_id:
                                # Añadir información de TTL
                                ttl = await client.ttl(key)
                                data['remaining_ttl'] = ttl if ttl > 0 else 0
                                sessions[session_id] = data
                    except Exception:
                        continue
                
                if cursor == 0:
                    break
            
            return sessions
            
        except Exception as e:
            self.logger.error(f"Error obteniendo sesiones activas: {e}")
            return {}
    
    async def get_session_count(self) -> int:
        """Obtiene el número total de sesiones activas"""
        try:
            client = await self.redis.connect()
            pattern = f"{self.session_prefix}*"
            
            cursor = 0
            count = 0
            
            while True:
                cursor, keys = await client.scan(cursor, match=pattern, count=100)
                count += len(keys)
                
                if cursor == 0:
                    break
            
            return count
            
        except Exception as e:
            self.logger.error(f"Error contando sesiones: {e}")
            return 0

# Instancia global del servicio
session_service = SessionService()
""" Instancia global del servicio de sesiones """