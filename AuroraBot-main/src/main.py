"""
Motor principal de Aura - Manejo de voz y procesamiento de comandos
(versión con TTS no bloqueante, stop_tts y detección de interrupción)
"""
import speech_recognition as sr
from gtts import gTTS
import os
import platform
import time
import logging
import threading
import subprocess
from queue import Queue, Empty
from pathlib import Path

from config.settings import (
    VOICE_LANG, TTS_LANG, TEMP_AUDIO_FILE,
    ENERGY_THRESHOLD, DYNAMIC_ENERGY, LISTEN_TIMEOUT,
    PHRASE_TIME_LIMIT, AMBIENT_NOISE_DURATION,
    EXIT_COMMANDS, get_audio_player
)

from src.cerebro_ia import generar_respuesta
from src.habilidades_sistema import abrir_programa
from src.habilidades_web import abrir_pagina_web, buscar_en_google

logger = logging.getLogger(__name__)

# TTS worker globals
_tts_queue = Queue()
_tts_worker_thread = None
_tts_process = None
_tts_stop_event = threading.Event()
_tts_lock = threading.Lock()
_tts_playing_flag = threading.Event()

def _find_player_command():
    players = get_audio_player()
    if not players:
        return None
    if isinstance(players, list):
        for cmd in players:
            player_name = cmd.split()[0]
            if os.system(f'which {player_name} > /dev/null 2>&1') == 0:
                return cmd
    else:
        player_name = players.split()[0]
        if os.system(f'which {player_name} > /dev/null 2>&1') == 0:
            return players
    return None

def _tts_worker():
    global _tts_process
    while True:
        try:
            text = _tts_queue.get()
        except Exception:
            break
        if text is None:
            break
        try:
            _tts_stop_event.clear()
            _tts_playing_flag.clear()
            tmp = Path(TEMP_AUDIO_FILE)
            # Generar audio
            tts = gTTS(text=text, lang=TTS_LANG)
            tts.save(str(tmp))
            player_cmd = _find_player_command()
            if player_cmd is None:
                # fallback: try ffplay via subprocess if available
                if os.system("which ffplay > /dev/null 2>&1") == 0:
                    cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", str(tmp)]
                elif os.system("which mpg123 > /dev/null 2>&1") == 0:
                    cmd = ["mpg123", str(tmp)]
                else:
                    logger.error("No audio player found")
                    _tts_playing_flag.clear()
                    try:
                        tmp.unlink()
                    except Exception:
                        pass
                    continue
            else:
                # split the command into program and args
                cmd = player_cmd.split() + [str(tmp)]
            with _tts_lock:
                try:
                    _tts_process = subprocess.Popen(cmd)
                except Exception as e:
                    logger.error(f"Error launching player: {e}")
                    _tts_process = None
                    try:
                        tmp.unlink()
                    except Exception:
                        pass
                    continue
                _tts_playing_flag.set()
            # loop while playing, allow stop signal
            while True:
                if _tts_stop_event.is_set():
                    with _tts_lock:
                        try:
                            if _tts_process and _tts_process.poll() is None:
                                _tts_process.terminate()
                        except Exception:
                            pass
                        _tts_process = None
                        _tts_playing_flag.clear()
                    break
                with _tts_lock:
                    if _tts_process is None:
                        break
                    if _tts_process.poll() is not None:
                        _tts_playing_flag.clear()
                        _tts_process = None
                        break
                time.sleep(0.05)
            try:
                tmp.unlink()
            except Exception:
                pass
        except Exception as e:
            logger.exception(f"TTS worker error: {e}")
            _tts_playing_flag.clear()
            try:
                tmp.unlink()
            except Exception:
                pass
            continue

def _start_tts_worker():
    global _tts_worker_thread
    if _tts_worker_thread is None or not _tts_worker_thread.is_alive():
        _tts_worker_thread = threading.Thread(target=_tts_worker, daemon=True)
        _tts_worker_thread.start()

def hablar(texto):
    if not texto:
        return
    _start_tts_worker()
    _tts_queue.put(limpiar_para_tts(texto))

def stop_tts():
    _tts_stop_event.set()
    with _tts_lock:
        try:
            if _tts_process and _tts_process.poll() is None:
                _tts_process.terminate()
        except Exception:
            pass
        _tts_process = None
    _tts_playing_flag.clear()

def tts_is_playing() -> bool:
    return _tts_playing_flag.is_set()

def limpiar_para_tts(texto: str) -> str:
    return texto.replace("\n", " ").strip()

def escuchar():
    r = sr.Recognizer()
    r.energy_threshold = ENERGY_THRESHOLD
    r.dynamic_energy_threshold = DYNAMIC_ENERGY
    try:
        with sr.Microphone() as source:
            # if TTS playing, stop it immediately before listening
            try:
                if tts_is_playing():
                    stop_tts()
                    # small wait to ensure player terminated
                    time.sleep(0.05)
            except Exception:
                pass
            r.adjust_for_ambient_noise(source, duration=AMBIENT_NOISE_DURATION)
            audio = r.listen(source, timeout=LISTEN_TIMEOUT, phrase_time_limit=PHRASE_TIME_LIMIT)
            comando = r.recognize_google(audio, language=VOICE_LANG)
            return comando.lower()
    except sr.WaitTimeoutError:
        return None
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        logger.error(f"Recognition request error: {e}")
        return "ERROR_MIC"
    except OSError as e:
        logger.error(f"OS error accessing microphone: {e}")
        return "ERROR_MIC"
    except Exception as e:
        logger.exception(f"Unexpected error in escuchar: {e}")
        return "ERROR_MIC"

def procesar_comando(comando):
    if not comando or comando == "ERROR_MIC":
        return "", True
    if any(palabra in comando for palabra in EXIT_COMMANDS):
        return "¡Hasta luego! Fue un placer ayudarte.", False
    habilidades = [
        ("Sistema", abrir_programa),
        ("Web", abrir_pagina_web),
        ("Búsqueda", buscar_en_google)
    ]
    for nombre, funcion in habilidades:
        try:
            respuesta = funcion(comando)
            if respuesta:
                return respuesta, True
        except Exception:
            continue
    try:
        respuesta_ia = generar_respuesta(comando)
        return respuesta_ia, True
    except Exception as e:
        logger.exception(f"Error generating AI response: {e}")
        return "Lo siento, tuve un problema procesando tu solicitud.", True

def modo_terminal():
    print("=" * 60)
    print("🎯 AURA - Asistente de IA")
    print("=" * 60)
    hablar("Hola, soy Aura. Sistema iniciado en modo terminal.")
    while True:
        print("\n📝 Opciones:")
        print("  1. Hablar (voz)")
        print("  2. Escribir (texto)")
        print("  3. Salir")
        opcion = input("\n👉 Selecciona (1/2/3): ").strip()
        if opcion == "1":
            comando = escuchar()
        elif opcion == "2":
            comando = input("💬 Escribe tu comando: ").strip().lower()
        elif opcion == "3":
            comando = "salir"
        else:
            print("❌ Opción inválida")
            continue
        if comando == "ERROR_MIC":
            print("❌ Error de micrófono detectado")
            continue
        if comando:
            respuesta, continuar = procesar_comando(comando)
            if respuesta:
                print(f"\n🤖 Aura: {respuesta}\n")
                hablar(respuesta)
            if not continuar:
                break
    print("\n👋 ¡Hasta pronto!")

def test_sistema():
    print("=" * 60)
    print("🧪 TEST DE SISTEMA")
    print("=" * 60)
    print("\n1️⃣  Test de síntesis de voz...")
    hablar("Probando sistema de voz")
    time.sleep(1)
    print("✅ Test completado")
    print("\n2️⃣  Test de reconocimiento de voz...")
    print("   (Di algo en 5 segundos)")
    comando = escuchar()
    if comando:
        print(f"✅ Reconocido: {comando}")
    else:
        print("⚠️  No se detectó voz")
    print("\n3️⃣  Test de procesamiento...")
    respuesta, _ = procesar_comando("hola")
    print(f"✅ Respuesta: {respuesta[:50]}...")
    print("\n" + "=" * 60)
    print("🎉 Tests completados")
    print("=" * 60)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    import argparse
    parser = argparse.ArgumentParser(description="Aura - Asistente de IA")
    parser.add_argument("--terminal", action="store_true", help="Ejecutar en modo terminal")
    parser.add_argument("--test", action="store_true", help="Ejecutar tests del sistema")
    args = parser.parse_args()
    if args.test:
        test_sistema()
    elif args.terminal:
        modo_terminal()
    else:
        print("ℹ️  Ejecuta con --terminal para modo consola o --test para pruebas")
