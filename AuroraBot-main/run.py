#!/usr/bin/env python3
"""
Aura - Asistente de IA con Voz
Punto de entrada principal del programa

Uso:
    python run.py              # Inicia la interfaz gráfica
    python run.py --terminal   # Modo terminal/consola
    python run.py --test       # Ejecuta tests del sistema
    python run.py --help       # Muestra ayuda
"""

import sys
import argparse
import logging
from pathlib import Path

# Configurar logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "aura.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def mostrar_banner():
    """Muestra el banner de bienvenida"""
    banner = """
    ╔═══════════════════════════════════════════╗
    ║                                           ║
    ║             A U R A  -  I A               ║
    ║                                           ║
    ║      Asistente Inteligente con Voz        ║
    ║                                           ║
    ╚═══════════════════════════════════════════╝
    """
    print(banner)


def verificar_dependencias():
    """
    Verifica que las dependencias críticas estén instaladas
    
    Returns:
        bool: True si todas las dependencias están disponibles
    """
    dependencias_criticas = [
        ("PySide6", "Interfaz gráfica"),
        ("speech_recognition", "Reconocimiento de voz"),
        ("gtts", "Síntesis de voz"),
        ("openai", "Cliente OpenAI (para OpenRouter)"),
        ("dotenv", "Configuración")
    ]
    
    faltantes = []
    
    for modulo, descripcion in dependencias_criticas:
        try:
            __import__(modulo)
        except ImportError:
            faltantes.append((modulo, descripcion))
    
    if faltantes:
        logger.error("Dependencias faltantes detectadas")
        print("❌ Dependencias faltantes:")
        for modulo, descripcion in faltantes:
            print(f"   • {modulo} ({descripcion})")
        print("\n💡 Instala las dependencias con:")
        print("   pip install -r requirements.txt")
        return False
    
    logger.info("✅ Todas las dependencias están instaladas")
    return True


def verificar_configuracion():
    """
    Verifica que la configuración esté completa
    
    Returns:
        bool: True si la configuración es válida
    """
    from config.openrouter_client import is_api_configured
    
    if not is_api_configured():
        logger.warning("API de OpenRouter no configurada")
        print("⚠️  ADVERTENCIA: OPENROUTER_API_KEY no configurada")
        print("\n📝 Para configurar:")
        print("   1. Copia .env.example a .env")
        print("   2. Obtén tu API key en: https://openrouter.ai/")
        print("   3. Edita .env y pega tu API key")
        print("\n⚠️  El asistente funcionará con capacidades limitadas")
        
        respuesta = input("\n¿Deseas continuar de todos modos? (s/n): ")
        return respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']
    
    logger.info("✅ Configuración de API verificada")
    return True


def modo_interfaz():
    """Inicia la interfaz gráfica"""
    logger.info("Iniciando interfaz gráfica")
    print("🖥️  Iniciando interfaz gráfica...")
    from src.interfaz import main
    main()


def modo_terminal():
    """Inicia el modo terminal"""
    logger.info("Iniciando modo terminal")
    print("💻 Iniciando modo terminal...")
    from src.main import modo_terminal
    modo_terminal()


def modo_test():
    """Ejecuta los tests del sistema"""
    logger.info("Ejecutando tests")
    print("🧪 Ejecutando tests...")
    from src.main import test_sistema
    test_sistema()


def main():
    """Función principal"""
    parser = argparse.ArgumentParser(
        description="Aura - Asistente de IA con Voz",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python run.py              Inicia la interfaz gráfica
  python run.py --terminal   Modo terminal/consola
  python run.py --test       Ejecuta tests del sistema
  python run.py --version    Muestra la versión
        """
    )
    
    parser.add_argument(
        "--terminal",
        action="store_true",
        help="Ejecutar en modo terminal (sin interfaz gráfica)"
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Ejecutar tests del sistema"
    )
    
    parser.add_argument(
        "--version",
        action="store_true",
        help="Mostrar versión del programa"
    )
    
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Omitir verificación de dependencias y configuración"
    )
    
    args = parser.parse_args()
    
    mostrar_banner()
    
    # Mostrar versión
    if args.version:
        print("Versión: 3.0.0 (OpenRouter Edition)")
        print("Python:", sys.version.split()[0])
        return
    
    if not args.skip_checks:
        print("🔍 Verificando dependencias...")
        if not verificar_dependencias():
            sys.exit(1)
        
        print("✅ Dependencias OK\n")
        
        print("🔍 Verificando configuración...")
        if not verificar_configuracion():
            print("\n❌ Configuración incompleta. Abortando.")
            sys.exit(1)
        
        print("✅ Configuración OK\n")
    
    # Ejecutar modo seleccionado
    try:
        if args.test:
            modo_test()
        elif args.terminal:
            modo_terminal()
        else:
            modo_interfaz()
    except KeyboardInterrupt:
        logger.info("Programa interrumpido por el usuario")
        print("\n\n👋 Programa interrumpido por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        print(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()