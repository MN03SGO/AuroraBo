"""
Cliente OpenRouter - Integración con OpenAI SDK
Configurado para usar DeepSeek y otros modelos a través de OpenRouter
"""
import os
from typing import Optional, List, Dict
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Importar OpenAI SDK moderno
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  openai>=1.0.0 no instalado. Instala con: pip install openai>=1.0.0")


# ============== CONFIGURACIÓN ==============
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "deepseek/deepseek-chat")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Configuración opcional
APP_NAME = os.getenv("APP_NAME", "Aura-Assistant")
SITE_URL = os.getenv("SITE_URL", "")


# ============== CLIENTE OPENROUTER ==============
class OpenRouterClient:
    """Cliente para interactuar con OpenRouter"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Inicializa el cliente de OpenRouter
        
        Args:
            api_key: API key de OpenRouter (usa variable de entorno si no se provee)
            model: Modelo a usar (por defecto: deepseek/deepseek-chat)
        """
        self.api_key = api_key or OPENROUTER_API_KEY
        self.model = model or OPENROUTER_MODEL
        self.client = None
        
        if not OPENAI_AVAILABLE:
            raise ImportError("openai>=1.0.0 es requerido. Instala con: pip install openai>=1.0.0")
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY no configurada en .env")
        
        # Inicializar cliente OpenAI apuntando a OpenRouter
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": SITE_URL or "http://localhost:3000",
                "X-Title": APP_NAME,
            }
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = 500,  # Limitar tokens para respuestas más rápidas
        stream: bool = False
    ) -> str:
        """
        Genera una respuesta usando el modelo configurado
        
        Args:
            messages: Lista de mensajes en formato [{"role": "user", "content": "..."}]
            temperature: Creatividad de la respuesta (0.0 - 2.0)
            max_tokens: Límite de tokens en la respuesta (500 por defecto para rapidez)
            stream: Si True, retorna un generador para streaming
            
        Returns:
            str: Respuesta del modelo
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=stream
            )
            
            if stream:
                return response  # Retorna el generador para streaming
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise RuntimeError(f"Error al generar respuesta: {e}")
    
    def simple_chat(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Interfaz simplificada para un solo mensaje
        
        Args:
            prompt: Pregunta o mensaje del usuario
            system_prompt: Prompt de sistema opcional
            
        Returns:
            str: Respuesta del modelo
        """
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        return self.chat(messages)
    
    def is_configured(self) -> bool:
        """Verifica si el cliente está correctamente configurado"""
        return bool(self.api_key and self.client)
    
    def get_model_info(self) -> Dict[str, str]:
        """Obtiene información sobre la configuración actual"""
        return {
            "provider": "OpenRouter",
            "model": self.model,
            "configured": self.is_configured(),
            "base_url": OPENROUTER_BASE_URL
        }


# ============== INSTANCIA GLOBAL ==============
# Cliente singleton para uso en todo el proyecto
_client_instance: Optional[OpenRouterClient] = None


def get_client() -> OpenRouterClient:
    """
    Obtiene o crea la instancia global del cliente
    
    Returns:
        OpenRouterClient: Instancia del cliente
    """
    global _client_instance
    
    if _client_instance is None:
        _client_instance = OpenRouterClient()
    
    return _client_instance


def is_api_configured() -> bool:
    """
    Verifica si la API está configurada
    
    Returns:
        bool: True si la API key está disponible
    """
    return bool(OPENROUTER_API_KEY and OPENAI_AVAILABLE)


def generar_respuesta(prompt: str, system_prompt: Optional[str] = None) -> str:
    """
    Función de conveniencia para generar respuestas
    
    Args:
        prompt: Pregunta o mensaje del usuario
        system_prompt: Prompt de sistema opcional
        
    Returns:
        str: Respuesta del modelo
    """
    if not is_api_configured():
        return "❌ OpenRouter no está configurado. Verifica tu API key en .env"
    
    try:
        client = get_client()
        return client.simple_chat(prompt, system_prompt)
    except Exception as e:
        return f"❌ Error al generar respuesta: {e}"


# ============== TEST ==============
if __name__ == "__main__":
    print("=" * 60)
    print(" TEST DEL CLIENTE OPENROUTER")
    print("=" * 60)
    
    # Test 1: Verificar configuración
    print("\n1️⃣  Verificando configuración...")
    if is_api_configured():
        print("   ✅ API configurada correctamente")
        
        try:
            client = get_client()
            info = client.get_model_info()
            print(f"   📡 Provider: {info['provider']}")
            print(f"   🤖 Model: {info['model']}")
            print(f"   🔗 Base URL: {info['base_url']}")
        except Exception as e:
            print(f"   ❌ Error al inicializar cliente: {e}")
            exit(1)
    else:
        print("   ❌ API no configurada")
        print("   💡 Configura OPENROUTER_API_KEY en tu archivo .env")
        exit(1)
    
    # Test 2: Probar generación de respuesta
    print("\n2️⃣  Probando generación de respuesta...")
    pregunta = "Di 'OK' si puedes escucharme"
    print(f"   Pregunta: {pregunta}")
    
    try:
        respuesta = generar_respuesta(pregunta)
        print(f"   Respuesta: {respuesta}")
        print("   ✅ Test exitoso")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print(" Tests completados")
    print("=" * 60)