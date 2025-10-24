#!/bin/bash

# ============================================
# Script de instalación automática de Aura
# ============================================

set -e  # Salir si hay algún error

echo "============================================"
echo "     INSTALADOR DE AURA - ASISTENTE IA"
echo "============================================"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir con color
print_success() {
    echo -e "${GREEN} $1${NC}"
}

print_error() {
    echo -e "${RED} $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}  $1${NC}"
}

# Detectar sistema operativo
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
fi

print_info "Sistema operativo detectado: $OS"
echo ""

# Verificar Python
echo " Verificando Python..."
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 no está instalado"
    echo "   Instala Python 3.8 o superior desde: https://www.python.org/"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION encontrado"
echo ""

# Verificar pip
echo "Verificando pip..."
if ! command -v pip3 &> /dev/null; then
    print_error "pip no está instalado"
    exit 1
fi
print_success "pip encontrado"
echo ""

# Instalar dependencias del sistema según OS
if [[ "$OS" == "linux" ]]; then
    echo " Instalando dependencias del sistema (Linux)..."
    print_info "Esto puede requerir permisos de administrador"
    
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install -y portaudio19-dev python3-pyaudio mpg123 ffmpeg
        print_success "Dependencias del sistema instaladas"
    elif command -v yum &> /dev/null; then
        sudo yum install -y portaudio-devel python3-pyaudio mpg123 ffmpeg
        print_success "Dependencias del sistema instaladas"
    else
        print_warning "Gestor de paquetes no reconocido"
        print_info "Instala manualmente: portaudio19-dev, python3-pyaudio, mpg123"
    fi
    echo ""
    
elif [[ "$OS" == "macos" ]]; then
    echo " Instalando dependencias del sistema (macOS)..."
    if ! command -v brew &> /dev/null; then
        print_warning "Homebrew no está instalado"
        print_info "Instala Homebrew desde: https://brew.sh/"
    else
        brew install portaudio mpg123 ffmpeg
        print_success "Dependencias del sistema instaladas"
    fi
    echo ""
fi

# Crear entorno virtual
echo " Creando entorno virtual..."
if [ -d ".venv" ]; then
    print_warning "El entorno virtual ya existe"
    read -p "¿Deseas recrearlo? (s/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        rm -rf .venv
        python3 -m venv .venv
        print_success "Entorno virtual recreado"
    fi
else
    python3 -m venv .venv
    print_success "Entorno virtual creado"
fi
echo ""

# Activar entorno virtual
echo " Activando entorno virtual..."
source .venv/bin/activate
print_success "Entorno virtual activado"
echo ""

# Actualizar pip
echo "⬆  Actualizando pip..."
pip install --upgrade pip > /dev/null 2>&1
print_success "pip actualizado"
echo ""

# Instalar dependencias de Python
echo " Instalando dependencias de Python..."
print_info "Esto puede tomar unos minutos..."

if pip install -r requirements.txt; then
    print_success "Dependencias de Python instaladas"
else
    print_error "Error al instalar dependencias"
    print_info "Intenta instalar manualmente: pip install -r requirements.txt"
    exit 1
fi
echo ""

# Configurar .env
echo "  Configurando archivo .env..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    print_success "Archivo .env creado desde .env.example"
    print_warning "IMPORTANTE: Edita .env y agrega tu OPENROUTER_API_KEY"
else
    print_info "El archivo .env ya existe (no se modificó)"
fi
echo ""

# Crear directorios necesarios
echo " Creando directorios..."
mkdir -p logs
mkdir -p assets
print_success "Directorios creados"
echo ""

# Verificar instalación
echo "🧪 Verificando instalación..."
if python run.py --version > /dev/null 2>&1; then
    print_success "Instalación verificada correctamente"
else
    print_warning "Verificación con advertencias (puede ser normal)"
fi
echo ""

# Resumen
echo "============================================"
echo "        INSTALACIÓN COMPLETADA"
echo "============================================"
echo ""
print_success "Aura está listo para usar"
echo ""
echo "📝 PRÓXIMOS PASOS:"
echo ""
echo "1️⃣  Obtén tu API key de OpenRouter:"
echo "   https://openrouter.ai/"
echo ""
echo "2️⃣  Edita el archivo .env y agrega tu API key:"
echo "   nano .env"
echo ""
echo "3️⃣  Ejecuta Aura:"
echo "   python run.py"
echo ""
echo "💡 COMANDOS ÚTILES:"
echo "   python run.py              # Interfaz gráfica"
echo "   python run.py --terminal   # Modo terminal"
echo "   python run.py --test       # Ejecutar tests"
echo ""
echo "📚 Documentación completa: README.md"
echo "🚀 Guía rápida: QUICK_START.md"
echo ""
echo "============================================"

# Preguntar si desea ejecutar ahora
read -p "¿Deseas ejecutar Aura ahora? (s/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Ss]$ ]]; then
    python run.py
fi