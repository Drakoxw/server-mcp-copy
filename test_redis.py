"""
Script para probar la conexión con Redis
"""
import asyncio
import json
import os
from dotenv import load_dotenv
load_dotenv()

from src.infrastructure.session.session_service import SessionStatus, session_service

from src.application.auth.oauth_service import create_oauth_url
from src.infrastructure.config.redis_config import redis_client

async def test_redis_connection():
    """Prueba la conexión con Redis"""
    try:
        print("🔄 Probando conexión con Redis...")
        print(f"Host: {os.getenv('REDIS_HOST', 'redis')}")
        print(f"Port: {os.getenv('REDIS_PORT', '6379')}")
        
        # Probar conexión
        client = await redis_client.connect()
        
        # Probar operaciones básicas
        test_key = "test_session:123"
        test_data = {
            "session_id": "123",
            "status": "pending",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        await client.setex(test_key, 60, json.dumps(test_data))
        print(f"✅ Datos guardados en: {test_key}")
        
        # Leer datos
        value = await client.get(test_key)
        if value:
            parsed_value = json.loads(value)
            print(f"✅ Datos leídos: {parsed_value}")
        
        # Limpiar
        await client.delete(test_key)
        print("✅ Datos limpiados")
        
        # Información del servidor
        health = await redis_client.health_check()
        print("📊 Estado de Redis:")
        for key, val in health.items():
            print(f"  {key}: {val}")

        oauth = await create_oauth_url()
        session_id = oauth['session_id']
        print(f"Oauth data: {oauth}")

        data_sesion = await session_service.get_session(session_id)
        print(f"✅ Datos sesion: {data_sesion}")
          # Limpiar
        await client.delete()
        print("✅ Datos limpiados")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_multiple_event_loops():
    """Prueba conexiones desde múltiples event loops"""
    print("\n🔄 Probando múltiples event loops...")
    
    async def worker(worker_id):
        try:
            client = await redis_client.connect()
            test_key = f"worker:{worker_id}"
            await client.set(test_key, f"data_from_worker_{worker_id}", ex=30)
            value = await client.get(test_key)
            print(f"Worker {worker_id}: {value}")
            await client.delete(test_key)
            return True
        except Exception as e:
            print(f"Worker {worker_id} error: {e}")
            return False
    
    # Crear múltiples tareas
    tasks = [worker(i) for i in range(3)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success_count = sum(1 for r in results if r is True)
    print(f"✅ {success_count}/3 workers exitosos")

if __name__ == "__main__":
    async def main():
        await test_redis_connection()
        await test_multiple_event_loops()
        await redis_client.disconnect_all()
    
    asyncio.run(main())