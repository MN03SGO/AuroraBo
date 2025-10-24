"""
Paquete de configuración de Aura
"""
from .settings import (
    ASSISTANT_NAME,
    ASSISTANT_PROMPT,
    VOICE_LANG,
    TTS_LANG,
    TEMP_AUDIO_FILE,
    EXIT_COMMANDS,
    WINDOW_TITLE,
    THEME_COLORS,
    get_programas_for_os,
    get_audio_player,
)

from .openrouter_client import (
    OpenRouterClient,
    get_client,
    is_api_configured,
    generar_respuesta,
)

__all__ = [
    # Settings
    "ASSISTANT_NAME",
    "ASSISTANT_PROMPT",
    "VOICE_LANG",
    "TTS_LANG",
    "TEMP_AUDIO_FILE",
    "EXIT_COMMANDS",
    "WINDOW_TITLE",
    "THEME_COLORS",
    "get_programas_for_os",
    "get_audio_player",
    # OpenRouter Client
    "OpenRouterClient",
    "get_client",
    "is_api_configured",
    "generar_respuesta",
]