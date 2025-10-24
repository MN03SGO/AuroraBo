"""
Configuración centralizada del proyecto Aura
"""
import os
import platform
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# ============== RUTAS DEL PROYECTO ==============
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
CONFIG_DIR = PROJECT_ROOT / "config"
ASSETS_DIR = PROJECT_ROOT / "assets"
LOGS_DIR = PROJECT_ROOT / "logs"

# Crear directorios si no existen
LOGS_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)

# ============== CONFIGURACIÓN DE IA ==============
ASSISTANT_NAME = "Aurora"
ASSISTANT_PROMPT = f"""
Actúa como {ASSISTANT_NAME}, una asistente de IA brillante, servicial y amigable.
Características:
- Eres concisa pero completa en tus respuestas
- Usas un tono profesional pero cercano
- Si no sabes algo, lo admites honestamente
- Siempre intentas ser útil y proactiva

IMPORTANTE para respuestas de voz:
- NO uses formato markdown (nada de asteriscos, guiones bajos, hashtags)
- NO uses emojis
- NO uses negritas ni cursivas
- Escribe todo en texto plano y natural
- Si necesitas énfasis, usa palabras descriptivas en lugar de formato
""".strip()

# ============== CONFIGURACIÓN DE VOZ ==============
VOICE_LANG = "es-ES"  # Reconocimiento de voz
TTS_LANG = "es"       # Text-to-Speech

ENERGY_THRESHOLD = 3000
DYNAMIC_ENERGY = False
LISTEN_TIMEOUT = 5
PHRASE_TIME_LIMIT = 10
AMBIENT_NOISE_DURATION = 1

# ============== CONFIGURACIÓN DE AUDIO ==============
TEMP_AUDIO_FILE = "temp_audio.mp3"
AUDIO_PLAYERS = {
    "Windows": "start",
    "Darwin": "afplay",
    "Linux": ["mpg123", "ffplay -nodisp -autoexit", "vlc --play-and-exit"]
}

# ============== CONFIGURACIÓN DE SISTEMA ==============
CURRENT_OS = platform.system()

PROGRAMAS_CONFIG = {
    "Windows": {
        "navegador": "start firefox",
        "firefox": "start firefox",
        "chrome": "start chrome",
        "edge": "start msedge",
        "notepad": "notepad",
        "calculadora": "calc",
        "explorador": "explorer",
        "paint": "mspaint",
        "word": "start winword",
        "excel": "start excel",
        "cmd": "start cmd",
        "powershell": "start powershell",
    },
    "Darwin": {  # macOS
        "navegador": "open -a Firefox",
        "firefox": "open -a Firefox",
        "safari": "open -a Safari",
        "chrome": "open -a 'Google Chrome'",
        "notas": "open -a Notes",
        "calculadora": "open -a Calculator",
        "terminal": "open -a Terminal",
        "finder": "open -a Finder",
        "vscode": "open -a 'Visual Studio Code'",
    },
    "Linux": {
        "navegador": "firefox",
        "firefox": "firefox",
        "chrome": "google-chrome",
        "chromium": "chromium-browser",
        "calculadora": "gnome-calculator",
        "terminal": "gnome-terminal",
        "gedit": "gedit",
        "nautilus": "nautilus",
        "vscode": "code",
        "code": "code",
    }
}

# ============== CONFIGURACIÓN WEB ==============
WEB_SHORTCUTS = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://www.twitter.com",
    "instagram": "https://www.instagram.com",
    "github": "https://www.github.com",
    "stackoverflow": "https://stackoverflow.com",
    "reddit": "https://www.reddit.com",
    "wikipedia": "https://www.wikipedia.org",
    "whatsapp": "https://web.whatsapp.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.com",
    "mercadolibre": "https://www.mercadolibre.com",
}

FIREFOX_PROFILE_PATH = os.getenv("FIREFOX_PROFILE_PATH", "")
USE_SELENIUM = os.getenv("USE_SELENIUM", "false").lower() == "true"

# ============== COMANDOS DE SALIDA ==============
EXIT_COMMANDS = [
    "adiós", "adios", "chao", "chau",
    "termina", "terminar", "finalizar",
    "cierra", "cerrar", "cierra el programa",
    "salir", "exit", "quit", "eso es todo"
]

# ============== CONFIGURACIÓN DE INTERFAZ ==============
WINDOW_TITLE = f"{ASSISTANT_NAME} - Asistente IA"
WINDOW_WIDTH = 1100
WINDOW_HEIGHT = 700
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600

THEME_COLORS = {
    "background_gradient_start": "#1e1b4b",
    "background_gradient_end": "#312e81",
    "primary_gradient_start": "#a855f7",
    "primary_gradient_end": "#ec4899",
    "hover_gradient_start": "#c084fc",
    "hover_gradient_end": "#f472b6",
    "text_primary": "#ffffff",
    "text_secondary": "#e5e7eb",
    "surface": "#374151",
    "surface_light": "#4b5563",
}

# ============== LOGGING ==============
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "aura.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# ============== FUNCIONES AUXILIARES ==============
def get_programas_for_os():
    """Retorna el diccionario de programas para el OS actual"""
    return PROGRAMAS_CONFIG.get(CURRENT_OS, {})


def get_audio_player():
    """Retorna el comando del reproductor de audio para el OS actual"""
    player = AUDIO_PLAYERS.get(CURRENT_OS)
    if isinstance(player, list):
        return player
    return [player] if player else []