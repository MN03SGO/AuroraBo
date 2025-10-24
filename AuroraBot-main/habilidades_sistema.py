# habilidades_sistema.py
import subprocess
import re

COMANDOS = {
    "navegador": "firefox",
    "chrome": "google-chrome-stable",
    "código": "code",
    "terminal": "konsole",
    "archivos": "dolphin"
}

def abrir_programa(comando, hablar, escuchar_confirmacion):
    app = comando.replace('abrir', '').strip()
    if app in COMANDOS:
        hablar(f"Abriendo {app}.")
        subprocess.Popen(COMANDOS[app])
    else:
        hablar(f"Disculpa, no encontré el programa '{app}'. ¿Quieres que lo busque en Google?")
        if escuchar_confirmacion():
            import pywhatkit
            hablar(f"Ok, buscando '{app}'.")
            pywhatkit.search(app)
        else:
            hablar("De acuerdo.")

def ajustar_volumen(comando, hablar):
    match = re.search(r'(\d+)', comando)
    if match:
        porcentaje = match.group(1)
        hablar(f"Ajustando volumen al {porcentaje} por ciento.")
        subprocess.run(['amixer', '-D', 'pulse', 'sset', 'Master', f'{porcentaje}%'])
    else:
        hablar("No entendí a qué porcentaje ajustar el volumen.")

def vaciar_papelera(hablar, escuchar_confirmacion):
    hablar("¿Estás totalmente seguro de que quieres vaciar la papelera? Esta acción es irreversible.")
    if escuchar_confirmacion():
        hablar("Vaciando la papelera.")
        subprocess.run(['trash-empty']) # Usa el comando de sistema
    else:
        hablar("De acuerdo, acción cancelada.")

def mover_a_papelera(comando, hablar, escuchar_confirmacion):
    archivo = comando.replace('borra el archivo', '').strip()
    hablar(f"Esta acción enviará '{archivo}' a la papelera. ¿Estás seguro?")
    if escuchar_confirmacion():
        try:
            subprocess.run(['trash-put', archivo], check=True)
            hablar(f"Hecho. '{archivo}' está en la papelera.")
        except (FileNotFoundError, subprocess.CalledProcessError):
            hablar(f"No pude encontrar el archivo '{archivo}'. Asegúrate de que el nombre o la ruta son correctos.")
    else:
        hablar("Acción cancelada.")

def buscar_archivo(comando, hablar):
    archivo = comando.replace('busca el archivo', '').strip()
    hablar(f"Buscando '{archivo}' en tu sistema. Esto puede tardar un momento.")
    subprocess.Popen(['kfind', '--search', archivo])