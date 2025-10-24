
import google.generativeai as genai

try:
    API_KEY = 'AIzaSyBmD9hvbNTyegjZwrJUNibGJ0klEXeNHvU'
    
    genai.configure(api_key=API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    
    # Si las dos líneas de arriba funcionan, la conexión fue exitosa.
    print("Cerebro de Google Gemini AI conectado exitosamente.")

except Exception as e:

    print(f"Error al conectar con Gemini AI: {e}")
    model = None

def generar_respuesta(pregunta):
    if model is None:
        return "Lo siento, mi cerebro no está conectado. Revisa la clave API y el error en la terminal."
    try:
        prompt_completo = (
            "Actúa como Aura, una asistente de IA brillante, servicial y con una personalidad energética. "
            "Tu objetivo es ayudar al usuario de la forma más clara y eficiente posible. "
            f"El usuario te ha preguntado: '{pregunta}'"
        )
        response = model.generate_content(prompt_completo)
        return response.text.replace('*', '')
    except Exception as e:
        print(f"Error de Gemini: {e}")
        return "Tuve un problema al procesar esa pregunta desde mi cerebro."