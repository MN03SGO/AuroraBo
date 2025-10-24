"""
Habilidades del sistema - Control de aplicaciones multiplataforma
"""
import subprocess
import re
import shutil
import logging
from config.settings import CURRENT_OS, get_programas_for_os

# Configurar logging
logger = logging.getLogger(__name__)


def abrir_programa(comando):
    """
    Abre un programa del sistema según el comando del usuario
    
    Args:
        comando (str): Comando de voz del usuario
        
    Returns:
        str: Mensaje de confirmación o vacío si no se encontró el programa
    """
    programas = get_programas_for_os()
    
    # Buscar coincidencias en los aliases
    for alias, ejecutable in programas.items():
        # Usar regex para buscar palabras completas
        patron = r'\b' + re.escape(alias) + r'\b'
        
        if re.search(patron, comando.lower()):
            return ejecutar_programa(alias, ejecutable)
    
    return ""


def ejecutar_programa(nombre, ejecutable):
    """
    Ejecuta un programa y maneja los errores
    
    Args:
        nombre (str): Nombre amigable del programa
        ejecutable (str): Comando o ruta del ejecutable
        
    Returns:
        str: Mensaje de confirmación o error
    """
    try:
        # Verificar si el ejecutable existe
        if not verificar_ejecutable(ejecutable):
            logger.warning(f"Programa no instalado: {nombre}")
            return f"Lo siento, {nombre} no está instalado en tu sistema."
        
        # Ejecutar según el sistema operativo
        if CURRENT_OS == "Windows":
            subprocess.Popen(ejecutable, shell=True)
        elif CURRENT_OS == "Darwin":  # macOS
            subprocess.Popen(ejecutable, shell=True)
        else:  # Linux
            subprocess.Popen([ejecutable])
        
        logger.info(f"✅ Programa '{nombre}' abierto correctamente")
        return f"Abriendo {nombre}."
        
    except FileNotFoundError:
        logger.error(f"Ejecutable no encontrado: {ejecutable}")
        return f"No pude encontrar {nombre}. Verifica que esté instalado."
    except PermissionError:
        logger.error(f"Sin permisos para ejecutar: {ejecutable}")
        return f"No tengo permisos para abrir {nombre}."
    except Exception as e:
        logger.error(f"Error al abrir {nombre}: {e}")
        return f"Ocurrió un error al intentar abrir {nombre}."


def verificar_ejecutable(ejecutable):
    """
    Verifica si un ejecutable está disponible en el sistema
    
    Args:
        ejecutable (str): Nombre o ruta del ejecutable
        
    Returns:
        bool: True si existe y es ejecutable
    """
    # Extraer el comando base (sin argumentos)
    comando_base = ejecutable.split()[0]
    
    # Para macOS con comandos 'open -a'
    if comando_base == "open":
        return True
    
    # Para Windows con comandos que terminan en .exe o .cmd
    if CURRENT_OS == "Windows":
        if comando_base.endswith(('.exe', '.cmd')):
            return shutil.which(comando_base) is not None
        return True
    
    # Para Linux y otros sistemas
    return shutil.which(comando_base) is not None


def listar_programas_disponibles():
    """
    Lista todos los programas disponibles para el sistema actual
    
    Returns:
        list: Lista de tuplas (alias, ejecutable, disponible)
    """
    programas = get_programas_for_os()
    resultado = []
    
    for alias, ejecutable in programas.items():
        disponible = verificar_ejecutable(ejecutable)
        resultado.append((alias, ejecutable, disponible))
    
    return resultado


# ============== TEST ==============
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=" * 60)
    print("🖥️  TEST DE HABILIDADES DEL SISTEMA")
    print("=" * 60)
    
    print(f"\n📍 Sistema operativo: {CURRENT_OS}")
    
    # Test 1: Listar programas
    print("\n1️⃣  Programas disponibles:")
    programas_info = listar_programas_disponibles()
    
    disponibles = [p for p in programas_info if p[2]]
    no_disponibles = [p for p in programas_info if not p[2]]
    
    print(f"\n✅ Disponibles ({len(disponibles)}):")
    for alias, ejecutable, _ in disponibles[:5]:
        print(f"   • {alias} → {ejecutable}")
    
    if len(disponibles) > 5:
        print(f"   ... y {len(disponibles) - 5} más")
    
    if no_disponibles:
        print(f"\n❌ No disponibles ({len(no_disponibles)}):")
        for alias, ejecutable, _ in no_disponibles[:3]:
            print(f"   • {alias} → {ejecutable}")
    
    # Test 2: Probar comando
    print("\n2️⃣  Probando detección de comandos...")
    comandos_prueba = [
        "abre firefox",
        "abre el navegador",
        "abre la calculadora"
    ]
    
    for cmd in comandos_prueba:
        resultado = abrir_programa(cmd)
        if resultado:
            print(f"   ✅ '{cmd}' → {resultado}")
        else:
            print(f"   ❌ '{cmd}' → No detectado")
    
    print("\n" + "=" * 60)
    print("⚠️  NOTA: No se ejecutaron programas realmente")
    print("=" * 60)