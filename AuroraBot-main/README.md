# 🎯 Aura - Asistente de IA con Voz

Asistente inteligente multiplataforma con reconocimiento de voz, síntesis de voz e integración con OpenRouter (DeepSeek y otros modelos).

## ✨ Características

- 🎤 **Reconocimiento de voz** en español
- 🔊 **Síntesis de voz** con gTTS
- 🧠 **IA avanzada** vía OpenRouter (DeepSeek, Llama, GPT y más)
- 💬 **Interfaz gráfica** moderna con PySide6
- 🖥️ **Control de aplicaciones** del sistema
- 🌐 **Navegación web** y búsquedas en Google
- 🐧🪟🍎 **Multiplataforma** (Linux, Windows, macOS)

## 🚀 Instalación Rápida

### 1. Clonar el repositorio

```bash
git clone https://github.com/tuusuario/aura-assistant.git
cd aura-assistant
```

### 2. Crear entorno virtual

```bash
python -m venv .venv

# Linux/macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

**Nota para Linux:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio mpg123
```

**Nota para macOS:**
```bash
brew install portaudio
```

### 4. Configurar API de OpenRouter

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env y agregar tu API key
nano .env  # o usa tu editor favorito
```

Obtén tu API key GRATIS (con $1 de crédito) en: https://openrouter.ai/

### 5. Ejecutar

```bash
# Interfaz gráfica (recomendado)
python run.py

# Modo terminal
python run.py --terminal

# Tests
python run.py --test
```

## 💰 Costos de OpenRouter

- **DeepSeek**: ~$0.14 por millón de tokens (MUY BARATO)
- Con **$1 puedes tener miles de conversaciones**
- También hay **modelos GRATIS** disponibles

### Modelos recomendados:

```bash
# En tu .env, elige uno:

# Muy barato y bueno
OPENROUTER_MODEL=deepseek/deepseek-chat

# Gratis
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
OPENROUTER_MODEL=google/gemma-2-9b-it:free
```

## 📖 Uso

### Interfaz Gráfica

```bash
python run.py
```

Elige entre:
- **Modo Chat**: Escribe o habla tus mensajes
- **Modo Voz**: Conversación continua por voz

### Modo Terminal

```bash
python run.py --terminal
```

### Comandos de voz disponibles:

#### 📂 Abrir aplicaciones:
- "Abre Firefox"
- "Abre la calculadora"
- "Abre Visual Studio Code"

#### 🌐 Navegación web:
- "Abre YouTube"
- "Abre Google"
- "Busca recetas de pasta"

#### 💬 Conversación con IA:
- "Hola, ¿cómo estás?"
- "Explícame qué es Python"
- "Cuéntame un chiste"

#### 🚪 Salir:
- "Adiós"
- "Termina"
- "Salir"

## 🗂️ Estructura del Proyecto

```
aura-assistant/
├── config/
│   ├── __init__.py
│   ├── openrouter_client.py  # Cliente OpenRouter
│   └── settings.py            # Configuración general
├── src/
│   ├── __init__.py
│   ├── cerebro_ia.py          # Lógica de IA
│   ├── habilidades_sistema.py # Control de aplicaciones
│   ├── habilidades_web.py     # Navegación web
│   ├── interfaz.py            # Interfaz gráfica
│   └── main.py                # Motor principal
├── logs/                      # Logs de la aplicación
├── .env                       # Configuración (NO subir a git)
├── .env.example               # Plantilla de configuración
├── .gitignore
├── requirements.txt
├── run.py                     # Punto de entrada
└── README.md
```

## ⚙️ Configuración Avanzada

### Cambiar el modelo de IA

Edita `.env`:
```bash
OPENROUTER_MODEL=deepseek/deepseek-chat
```

### Habilitar Selenium (navegación avanzada)

```bash
# En .env
USE_SELENIUM=true

# Instalar dependencias
pip install selenium webdriver-manager
```

### Agregar programas personalizados

Edita `config/settings.py` en la sección `PROGRAMAS_CONFIG`.

### Agregar atajos web personalizados

Edita `config/settings.py` en la sección `WEB_SHORTCUTS`.

## 🐛 Solución de Problemas

### PyAudio no se instala

**Windows:**
```bash
pip install pipwin
pipwin install pyaudio
```

**macOS:**
```bash
brew install portaudio
pip install pyaudio
```

**Linux:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

### Error "No se encontró reproductor de audio" (Linux)

```bash
# Instalar reproductores
sudo apt-get install mpg123 ffmpeg vlc
```

### Error con el micrófono

1. Verifica que el micrófono esté conectado
2. Comprueba los permisos de audio
3. Linux: `sudo usermod -a -G audio $USER`

### La IA no responde

1. Verifica tu API key en `.env`
2. Comprueba tu conexión a internet
3. Revisa los logs en `logs/aura.log`

## 🔧 Desarrollo

### Ejecutar tests

```bash
python run.py --test
```

### Ver logs

```bash
tail -f logs/aura.log
```

### Modo debug

```bash
# En .env
LOG_LEVEL=DEBUG
```

## 📝 Licencia

Este proyecto está bajo la Licencia MIT.

## 🤝 Contribuciones

Las contribuciones son bienvenidas! Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📧 Contacto

Si tienes preguntas o sugerencias, abre un issue en GitHub.

## 🙏 Agradecimientos

- [OpenRouter](https://openrouter.ai/) - API de acceso a múltiples modelos de IA
- [DeepSeek](https://www.deepseek.com/) - Modelo de IA eficiente y económico
- [PySide6](https://www.qt.io/qt-for-python) - Framework de interfaz gráfica
- [gTTS](https://github.com/pndurette/gTTS) - Síntesis de voz
- [SpeechRecognition](https://github.com/Uberi/speech_recognition) - Reconocimiento de voz

---

⭐ Si te gusta este proyecto, dale una estrella en GitHub!