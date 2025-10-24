"""
Paquete principal de Aura - Asistente de IA
"""
from .cerebro_ia import generar_respuesta, verificar_conexion, obtener_info_api
from .habilidades_sistema import abrir_programa, listar_programas_disponibles
from .habilidades_web import abrir_pagina_web, buscar_en_google, listar_atajos_web
from .main import hablar, escuchar, procesar_comando, modo_terminal, test_sistema

__all__ = [
    # Cerebro IA
    "generar_respuesta",
    "verificar_conexion",
    "obtener_info_api",
    # Habilidades Sistema
    "abrir_programa",
    "listar_programas_disponibles",
    # Habilidades Web
    "abrir_pagina_web",
    "buscar_en_google",
    "listar_atajos_web",
    # Main
    "hablar",
    "escuchar",
    "procesar_comando",
    "modo_terminal",
    "test_sistema",
]