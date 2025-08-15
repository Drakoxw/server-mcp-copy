"""
Utilidad para monitorear el comportamiento de TTL en Redis
"""
import asyncio
import json
from datetime import datetime, timezone
from typing import Dict, List, Tuple
from dotenv import load_dotenv
load_dotenv()

class RedisSessionMonitor:
    """Monitor para verificar el comportamiento de TTL en Redis"""
    
    def __init__(self, session_service):
        self.session_service = session_service
        self.logger = session_service.logger
    
    async def monitor_ttl_behavior(self, duration_minutes: int = 5) -> Dict:
        """
        Monitorea el comportamiento de TTL durante un período determinado
        """
        stats = {
            'start_time': datetime.now(timezone.utc).isoformat(),
            'duration_minutes': duration_minutes,
            'snapshots': [],
            'redis_cleanups': 0,
            'manual_cleanups': 0
        }
        
        end_time = datetime.now(timezone.utc).timestamp() + (duration_minutes * 60)
        
        while datetime.now(timezone.utc).timestamp() < end_time:
            # Tomar snapshot del estado actual
            snapshot = await self._take_snapshot()
            stats['snapshots'].append(snapshot)
            
            self.logger.info(f"📊 Snapshot: {snapshot['active_sessions']} sesiones activas, "
                           f"{snapshot['expired_by_redis']} expiradas por Redis")
            
            # Ejecutar limpieza manual para comparar
            manual_cleaned = await self.session_service.cleanup_expired_sessions()
            stats['manual_cleanups'] += manual_cleaned
            
            if manual_cleaned > 0:
                self.logger.info(f"🧹 Limpieza manual eliminó {manual_cleaned} sesiones")
            
            await asyncio.sleep(15)  # Check cada 15 segundos
        
        stats['end_time'] = datetime.now(timezone.utc).isoformat()
        return stats
    
    async def _take_snapshot(self) -> Dict:
        """Toma un snapshot del estado actual de las sesiones"""
        try:
            client = await self.session_service.redis.connect()
            pattern = f"{self.session_service.session_prefix}*"
            
            cursor = 0
            total_keys = 0
            active_sessions = 0
            expired_by_redis = 0
            ttl_distribution = {'0-60s': 0, '1-5min': 0, '5-60min': 0, '1h+': 0}
            
            while True:
                cursor, keys = await client.scan(cursor, match=pattern, count=100)
                total_keys += len(keys)
                
                for key in keys:
                    try:
                        # Verificar si la clave existe (Redis pudo haberla eliminado)
                        exists = await client.exists(key)
                        if not exists:
                            expired_by_redis += 1
                            continue
                        
                        # Obtener TTL
                        ttl = await client.ttl(key)
                        
                        if ttl == -2:  # Clave no existe
                            expired_by_redis += 1
                        elif ttl == -1:  # Clave existe pero sin TTL
                            active_sessions += 1
                            ttl_distribution['1h+'] += 1
                        elif ttl > 0:
                            active_sessions += 1
                            # Clasificar por TTL
                            if ttl <= 60:
                                ttl_distribution['0-60s'] += 1
                            elif ttl <= 300:  # 5 min
                                ttl_distribution['1-5min'] += 1
                            elif ttl <= 3600:  # 1 hour
                                ttl_distribution['5-60min'] += 1
                            else:
                                ttl_distribution['1h+'] += 1
                        
                    except Exception:
                        expired_by_redis += 1
                
                if cursor == 0:
                    break
            
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'total_keys_found': total_keys,
                'active_sessions': active_sessions,
                'expired_by_redis': expired_by_redis,
                'ttl_distribution': ttl_distribution
            }
            
        except Exception as e:
            self.logger.error(f"Error tomando snapshot: {e}")
            return {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'error': str(e)
            }
    
    async def test_ttl_accuracy(self, test_ttl: int = 30) -> Dict:
        """
        Prueba la precisión del TTL creando sesiones de prueba
        """
        test_results = {
            'test_ttl': test_ttl,
            'sessions_created': [],
            'start_time': datetime.now(timezone.utc).isoformat()
        }
        
        # Crear 5 sesiones de prueba
        for i in range(5):
            session_data = {
                'test_session': True,
                'test_number': i,
                'created_at': datetime.now(timezone.utc).isoformat()
            }
            
            session_id = await self.session_service.create_session(
                session_data, 
                ttl=test_ttl
            )
            
            test_results['sessions_created'].append({
                'session_id': session_id,
                'created_at': datetime.now(timezone.utc).isoformat()
            })
        
        # Monitorear hasta que todas expiren
        expired_sessions = []
        start_time = datetime.now(timezone.utc).timestamp()
        
        while len(expired_sessions) < 5:
            current_time = datetime.now(timezone.utc).timestamp()
            
            # Verificar cada sesión
            for session_info in test_results['sessions_created']:
                session_id = session_info['session_id']
                
                if session_id not in [s['session_id'] for s in expired_sessions]:
                    session_data = await self.session_service.get_session(session_id)
                    
                    if session_data is None:  # Sesión expirada
                        expired_sessions.append({
                            'session_id': session_id,
                            'expired_at': datetime.now(timezone.utc).isoformat(),
                            'actual_lifetime': current_time - start_time
                        })
                        
                        self.logger.info(f"🕐 Sesión {session_id} expiró después de "
                                       f"{current_time - start_time:.1f}s")
            
            await asyncio.sleep(1)  # Check cada segundo
            
            # Timeout de seguridad
            if current_time - start_time > (test_ttl * 2):
                break
        
        test_results['expired_sessions'] = expired_sessions
        test_results['end_time'] = datetime.now(timezone.utc).isoformat()
        
        return test_results
    
    async def get_redis_memory_info(self) -> Dict:
        """Obtiene información de memoria de Redis"""
        try:
            client = await self.session_service.redis.connect()
            info = await client.info('memory')
            
            return {
                'used_memory': info.get('used_memory', 0),
                'used_memory_human': info.get('used_memory_human', '0B'),
                'used_memory_peak': info.get('used_memory_peak', 0),
                'used_memory_peak_human': info.get('used_memory_peak_human', '0B'),
                'maxmemory': info.get('maxmemory', 0),
                'maxmemory_human': info.get('maxmemory_human', 'unlimited'),
            }
            
        except Exception as e:
            self.logger.error(f"Error obteniendo info de memoria: {e}")
            return {'error': str(e)}

# Función para usar el monitor
async def run_redis_monitor_test():
    """Ejecuta un test completo de monitoreo de Redis"""
    from src.infrastructure.session.session_service import session_service
    
    monitor = RedisSessionMonitor(session_service)
    
    print("🔍 Iniciando monitoreo de TTL de Redis...")
    
    # Test 1: Monitoreo general
    print("\n📊 Test 1: Monitoreo general (2 minutos)...")
    stats = await monitor.monitor_ttl_behavior(duration_minutes=1)
    print(f"Resultados: {json.dumps(stats, indent=2)}")
    
    # Test 2: Precisión de TTL
    print("\n🕐 Test 2: Precisión de TTL (30 segundos)...")
    ttl_test = await monitor.test_ttl_accuracy(test_ttl=30)
    print(f"Resultados: {json.dumps(ttl_test, indent=2)}")
    
    # Test 3: Info de memoria
    print("\n💾 Test 3: Información de memoria...")
    memory_info = await monitor.get_redis_memory_info()
    print(f"Memoria: {json.dumps(memory_info, indent=2)}")

if __name__ == "__main__":
    asyncio.run(run_redis_monitor_test())