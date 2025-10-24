# main.py
import speech_recognition as sr
from gtts import gTTS
import os
import random


import cerebro_ia
import habilidades_web
import habilidades_sistema

def hablar(texto):
    print(f"Aura: {texto}")
    try:
        tts = gTTS(text=texto, lang='es', tld='com.mx', slow=False)
        tts.save("respuesta.mp3")
        os.system("mpg123 -q respuesta.mp3")
        os.remove("respuesta.mp3")
    except Exception as e:
        print(f"Ocurrió un error con la voz (gTTS): {e}.")

def escuchar(prompt="...", timeout=7):
    r = sr.Recognizer()
    with sr.Microphone(device_index=4) as source:
        print(prompt)
        r.pause_threshold = 0.8
        try:
            audio = r.listen(source, timeout=timeout, phrase_time_limit=5)
            print("Procesando tu voz...")
            query = r.recognize_google(audio, language='es-SV')
            print(f"Tú dijiste: {query}\n")
            return query.lower()
        except sr.WaitTimeoutError: return "timeout"
        except Exception: return "error"

def escuchar_confirmacion():
    respuesta = escuchar("Esperando confirmación (sí/no)...", timeout=4)
    return "sí" in respuesta or "claro" in respuesta

if __name__ == "__main__":
    PALABRA_CLAVE = "hola aura"
    hablar(f"Sistema Aura iniciado. Di '{PALABRA_CLAVE}' para comenzar.")

    while True:
        comando_inicial = escuchar(f"Esperando '{PALABRA_CLAVE}'...", timeout=10)

        if PALABRA_CLAVE in comando_inicial:
            hablar("¡Hola! Soy Aura. ¿En qué te puedo ayudar?")
            comando = escuchar()

            if comando in ["error", "timeout"]:
                hablar("Disculpa, no te entendí bien. ¿Podrías repetirlo?")
                continue

            if 'adiós' in comando:
                hablar("¡Claro! Que tengas un día genial.")
                break
            
            elif 'abrir' in comando:
                habilidades_sistema.abrir_programa(comando, hablar, escuchar_confirmacion)
            elif 'volumen a' in comando:
                habilidades_sistema.ajustar_volumen(comando, hablar)
            elif 'vaciar papelera' in comando:
                habilidades_sistema.vaciar_papelera(hablar, escuchar_confirmacion)
            elif 'borra el archivo' in comando:
                habilidades_sistema.mover_a_papelera(comando, hablar, escuchar_confirmacion)
            elif 'busca el archivo' in comando:
                habilidades_sistema.buscar_archivo(comando, hablar)

            elif 'busca en google' in comando:
                habilidades_web.buscar_en_google(comando, hablar)
            elif 'busca en youtube' in comando:
                habilidades_web.buscar_en_youtube(comando, hablar)
            elif 'clima' in comando:
                habilidades_web.buscar_clima(comando, hablar)

            else:
                respuesta = cerebro_ia.generar_respuesta(comando)
                hablar(respuesta)