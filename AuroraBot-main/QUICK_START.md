# 🚀 Guía de Inicio Rápido - Aura

## ⚡ En 5 minutos tendrás Aura funcionando

### Paso 1: Obtener API Key de OpenRouter (2 min)

1. Ve a: https://openrouter.ai/
2. Haz clic en "Sign In" (puedes usar GitHub)
3. Ve a "Keys" en el menú
4. Haz clic en "Create Key"
5. **Copia la key** (solo se muestra una vez)

💡 **Recibes $1 gratis** para empezar (miles de conversaciones)

---

### Paso 2: Instalar Aura (2 min)

```bash
# 1. Clonar
git clone https://github.com/tuusuario/aura-assistant.git
cd aura-assistant

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install -r requirements.txt
```

---

### Paso 3: Configurar (1 min)

```bash
# Copiar archivo de configuración
cp .env.example .env

# Editar y pegar tu API key
nano .env  # o usa tu editor favorito
```

Pega tu API key de OpenRouter:
```bash
OPENROUTER_API_KEY=sk-or-v1-tu-key-aqui
```

---

### Paso 4: ¡Listo! Ejecutar

```bash
python run.py
```

---

## 🎯 Primeros Comandos

### En la interfaz gráfica:

1. **Elige modo Chat o Voz**
2. Prueba estos comandos:

```
💬 En Chat:
- "Hola, ¿cómo estás?"
- "Explícame qué es Python"
- "Dame 3 consejos para aprender programación"

🎤 En Voz:
- Habla al micrófono: "Abre YouTube"
- "Busca recetas de pasta"
- "Abre Firefox"
```

---

## ❓ Problemas Comunes

### ❌ "PyAudio no se instala"

**Linux:**
```bash
sudo apt-get install portaudio19-dev python3-pyaudio
pip install pyaudio
```

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

---

### ❌ "No se encontró reproductor de audio" (Linux)

```bash
sudo apt-get install mpg123
```

---

### ❌ "OPENROUTER_API_KEY no configurada"

Verifica que:
1. Copiaste `.env.example` a `.env`
2. Pegaste tu API key correctamente
3. No hay espacios extra en la key

---

## 💡 Tips

### Cambiar el modelo de IA

En `.env`:
```bash
# Muy barato y bueno (recomendado)
OPENROUTER_MODEL=deepseek/deepseek-chat

# Gratis
OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

### Ver más modelos disponibles

https://openrouter.ai/models

### Modo terminal (sin interfaz gráfica)

```bash
python run.py --terminal
```

### Ejecutar tests

```bash
python run.py --test
```

---

## 📚 Siguiente Paso

Lee el [README.md](README.md) completo para:
- Configuración avanzada
- Agregar programas personalizados
- Habilitar Selenium
- Y mucho más

---

## 🆘 Ayuda

Si tienes problemas:
1. Revisa los logs: `logs/aura.log`
2. Ejecuta el test: `python run.py --test`
3. Abre un issue en GitHub

---

¡Disfruta de Aura! 🎉