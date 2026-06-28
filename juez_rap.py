import os
import json
from groq import Groq
from pydantic import BaseModel, Field

# 1. Definimos la estructura del veredicto
class VeredictoRap(BaseModel):
    puntuacion_total: float = Field(description="Calificación general de 1 a 10")
    analisis_tecnico: str = Field(description="Crítica detallada de rimas y métricas")
    punchline_destacado: str = Field(description="La mejor frase encontrada")
    veredicto_callejero: str = Field(description="Frase con actitud de juez de rap dictando el resultado")

# 2. Inicializamos el cliente de Groq
# Consigue tu API Key gratis en: https://groq.com
client = Groq(api_key=os.environ.get("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"))

def juez_de_rap_gratis(letra: str):
    prompt_sistema = (
        "Actúas como un juez profesional de batallas de rap (como en Red Bull o FMS). "
        "Debes responder ÚNICAMENTE con un objeto JSON válido que cumpla estrictamente con este esquema:\n"
        "{\n"
        "  \"puntuacion_total\": número de 1 a 10,\n"
        "  \"analisis_tecnico\": \"texto analizando rimas\",\n"
        "  \"punchline_destacado\": \"la mejor frase\",\n"
        "  \"veredicto_callejero\": \"frase con jerga y actitud de juez de rap\"\n"
        "}\n"
        "No agregues texto antes ni después del JSON."
    )

    # Usamos Llama 3.1 70B (un modelo open source potente y gratis en Groq)
    completion = client.chat.completions.create(
        model="llama-3.1-70b-versatile",
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": f"Evalúa estas barras:\n\n{letra}"}
        ],
        temperature=0.7,
        response_format={"type": "json_object"} # Fuerza a Llama a responder en JSON
    )
    
    # Parseamos la respuesta de texto a un diccionario de Python
    datos_json = json.loads(completion.choices[0].message.content)
    return VeredictoRap(**datos_json)

# 3. Prueba el Juez
if __name__ == "__main__":
    mis_barras = """
    Tengo el micro encendido, tu señal se congela,
    mi rima es de la calle, la tuya es de escuela.
    No me ganas con código, no me ganas con flow,
    se te apagan las luces cuando empiezo mi show.
    """
    
    try:
        resultado = juez_de_rap_gratis(mis_barras)
        print(f"🏅 Puntuación: {resultado.puntuacion_total}/10")
        print(f"🔥 Punchline: '{resultado.punchline_destacado}'")
        print(f"📝 Análisis: {resultado.analisis_tecnico}")
        print(f"🎤 Veredicto: {resultado.veredicto_callejero}")
    except Exception as e:
        print(f"Error al conectar u obtener el veredicto: {e}")

