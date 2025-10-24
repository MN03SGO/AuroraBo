"""
Cerebro de IA - Integración con OpenRouter
"""
import logging
from config.openrouter_client import is_api_configured, get_client
from config.settings import ASSISTANT_PROMPT

# Configurar logging
logger = logging.getLogger(__name__)


def generar_respuesta(pregunta: str) -> str:
    """
    Genera una respuesta usando OpenRouter (DeepSeek)
    
    Args:
        pregunta: Pregunta o comando del usuario
        
    Returns:
        str: Respuesta generada por la IA
    """
    if not is_api_configured():
        logger.warning("API de OpenRouter no configurada")
        return (
            "Lo siento, no puedo conectarme a OpenRouter en este momento. "
            "Verifica que hayas configurado OPENROUTER_API_KEY en el archivo .env"
        )
    
    try:
        logger.info(f"Generando respuesta para: {pregunta[:50]}...")
        
        # Obtener cliente y generar respuesta
        client = get_client()
        respuesta = client.simple_chat(
            prompt=pregunta,
            system_prompt=ASSISTANT_PROMPT
        )
        
        if not respuesta:
            logger.warning("Respuesta vacía recibida")
            return "Lo siento, no pude generar una respuesta. ¿Podrías reformular tu pregunta?"
        
        logger.info("Respuesta generada exitosamente")
        return respuesta
        
    except Exception as e:
        logger.error(f"Error al generar respuesta: {e}")
        return f"Lo siento, ocurrió un error al procesar tu solicitud: {str(e)}"


def verificar_conexion() -> bool:
    """
    Verifica que la conexión con OpenRouter esté funcionando
    
    Returns:
        bool: True si la conexión es exitosa
    """
    try:
        logger.info("Verificando conexión con OpenRouter...")
        respuesta = generar_respuesta("Di 'OK' si me escuchas")
        resultado = "ok" in respuesta.lower()
        
        if resultado:
            logger.info("✅ Conexión verificada correctamente")
        else:
            logger.warning("⚠️  Respuesta inesperada en verificación")
        
        return resultado
        
    except Exception as e:
        logger.error(f"Error en verificación de conexión: {e}")
        return False


def obtener_info_api() -> dict:
    """
    Obtiene información sobre la configuración de la API
    
    Returns:
        dict: Información de la API
    """
    try:
        if is_api_configured():
            client = get_client()
            info = client.get_model_info()
            info["conectado"] = True
            return info
        else:
            return {
                "provider": "OpenRouter",
                "disponible": False,
                "configurado": False,
                "conectado": False
            }
    except Exception as e:
        logger.error(f"Error al obtener info de API: {e}")
        return {
            "provider": "OpenRouter",
            "error": str(e),
            "conectado": False
        }


# ============== TEST ==============
if __name__ == "__main__":
    # Configurar logging para el test
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 60)
    print(" TEST DEL CEREBRO DE IA - OPENROUTER")
    print("=" * 60)
    
    # Test 1: Verificar configuración
    print("\n1️⃣  Verificando configuración...")
    info = obtener_info_api()
    for key, value in info.items():
        print(f"   {key}: {value}")
    
    # Test 2: Verificar conexión
    print("\n2️⃣  Verificando conexión...")
    if verificar_conexion():
        print("   ✅ Conexión OK")
    else:
        print("   ❌ Conexión fallida")
    
    # Test 3: Generar respuesta
    print("\n3️⃣  Generando respuesta de prueba...")
    pregunta = "Hola, ¿cómo estás?"
    print(f"   Pregunta: {pregunta}")
    respuesta = generar_respuesta(pregunta)
    print(f"   Respuesta: {respuesta}")
    
    print("\n" + "=" * 60)
    print(" Tests completados")
    print("=" * 60)