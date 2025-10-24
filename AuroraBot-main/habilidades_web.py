# habilidades_web.py
import pywhatkit

def buscar_en_google(comando, hablar):
 
    termino = comando.replace('busca en google', '').strip()
    hablar(f"Claro, buscando '{termino}' en Google.")
    pywhatkit.search(termino)

def buscar_en_youtube(comando, hablar):
  
    termino = comando.replace('busca en youtube', '').strip()
    hablar(f"Buscando '{termino}' en YouTube ahora mismo.")
    pywhatkit.playonyt(termino)

def buscar_clima(comando, hablar):
    lugar = comando.split("clima en")[-1].strip() if "en" in comando else "El Salvador"
    hablar(f"Claro, buscando el pronóstico del tiempo para {lugar}.")
    pywhatkit.search(f"clima en {lugar}")