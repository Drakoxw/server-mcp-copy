# logger_config.py
import logging
import logging.handlers
import os
from datetime import datetime
from pathlib import Path

class LoggerSetup:
    """Configurador de logger para el proyecto"""
    
    def __init__(self, 
                 name: str = "mcp_server_auth",
                 log_dir: str = "logs",
                 file_name: str = "app.log",
                 level: str = "INFO"):
        self.name = name
        self.log_dir = Path(log_dir)
        self.level = getattr(logging, level.upper())
        self.file_name = file_name
        
        # Crear directorio de logs si no existe
        self.log_dir.mkdir(exist_ok=True)
        
        # Configurar el logger principal
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Configura y retorna el logger principal"""
        
        # Crear logger
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)
        
        # Evitar duplicar handlers si ya existen
        if logger.handlers:
            return logger
        
        # Formato de los mensajes
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 1. Handler para archivo general (todos los logs)
        general_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / self.file_name,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        general_handler.setLevel(logging.DEBUG)
        general_handler.setFormatter(formatter)
        logger.addHandler(general_handler)
        
        # 2. Handler para errores específicos
        error_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / "errors.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
        
        # 3. Handler para consola (opcional, para desarrollo)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(levelname)s - %(name)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
        # 4. Handler para logs diarios (opcional)
        daily_handler = logging.handlers.TimedRotatingFileHandler(
            filename=self.log_dir / "daily.log",
            when='midnight',
            interval=1,
            backupCount=30,  # Mantener 30 días
            encoding='utf-8'
        )
        daily_handler.setLevel(logging.INFO)
        daily_handler.setFormatter(formatter)
        logger.addHandler(daily_handler)
        
        return logger
    
    def get_logger(self) -> logging.Logger:
        """Retorna el logger configurado"""
        return self.logger
    
    def create_module_logger(self, module_name: str) -> logging.Logger:
        """Crea un logger específico para un módulo"""
        return logging.getLogger(f"{self.name}.{module_name}")


# Ejemplo de uso simple
def setup_basic_logger(name: str = "app", log_file: str = "app.log"):
    """Configuración básica de logger"""
    
    # Crear directorio logs si no existe
    os.makedirs("logs", exist_ok=True)
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"logs/{log_file}", encoding='utf-8'),
            logging.StreamHandler()  # También mostrar en consola
        ]
    )
    
    return logging.getLogger(name)


# Configuración avanzada con diferentes niveles
def setup_advanced_logger():
    """Configuración avanzada con múltiples handlers"""
    
    # Crear directorio
    os.makedirs("logs", exist_ok=True)
    
    # Logger principal
    logger = logging.getLogger("mcp_auth_server")
    logger.setLevel(logging.DEBUG)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s'
    )
    
    # Handler para DEBUG y superiores
    debug_handler = logging.FileHandler("logs/debug.log", encoding='utf-8')
    debug_handler.setLevel(logging.DEBUG)
    debug_handler.setFormatter(formatter)
    
    # Handler solo para INFO y superiores
    info_handler = logging.FileHandler("logs/info.log", encoding='utf-8')
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(formatter)
    
    # Handler solo para ERRORES
    error_handler = logging.FileHandler("logs/error.log", encoding='utf-8')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(formatter)
    
    # Agregar handlers
    logger.addHandler(debug_handler)
    logger.addHandler(info_handler)
    logger.addHandler(error_handler)
    
    return logger


# Decorador para logging automático de funciones
def log_function_calls(logger):
    """Decorador para loggear entrada y salida de funciones"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            logger.info(f"Ejecutando función: {func.__name__}")
            logger.debug(f"Argumentos: args={args}, kwargs={kwargs}")
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"Función {func.__name__} ejecutada exitosamente")
                return result
            except Exception as e:
                logger.error(f"Error en función {func.__name__}: {str(e)}", exc_info=True)
                raise
        return wrapper
    return decorator


# Ejemplo de uso en tu aplicación
if __name__ == "__main__":
    # Opción 1: Logger básico
    basic_logger = setup_basic_logger("test_app", "test.log")
    basic_logger.info("Aplicación iniciada")
    basic_logger.error("Esto es un error de prueba")
    
    # Opción 2: Logger avanzado
    logger_setup = LoggerSetup("mcp_auth_server")
    main_logger = logger_setup.get_logger()
    
    # Crear loggers específicos para módulos
    auth_logger = logger_setup.create_module_logger("auth")
    api_logger = logger_setup.create_module_logger("api")
    
    # Ejemplos de uso
    main_logger.info("Servidor MCP iniciado")
    auth_logger.debug("Verificando credenciales OAuth")
    api_logger.warning("Rate limit cercano al límite")
    main_logger.error("Error crítico del sistema")
    
    # Uso del decorador
    @log_function_calls(main_logger)
    def ejemplo_funcion(param1, param2=None):
        return f"Procesado: {param1}, {param2}"
    
    resultado = ejemplo_funcion("test", param2="valor")