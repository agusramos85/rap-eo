import os
import json
import wave
import streamlit as st
from groq import Groq
from pydantic import BaseModel, Field
import streamlit.components.v1 as components
from streamlit_mic_recorder import mic_recorder

# Configuración de la página web
st.set_page_config(page_title="IA Rap Judge - Audio Edition", page_icon="🎤", layout="wide")

# --- FUNCIÓN PARA GENERAR UN WAV BASE VÁLIDO SI NO EXISTE ---
def inicializar_archivo_wav(nombre_archivo="mi_freestyle.wav"):
    if not os.path.exists(nombre_archivo):
        frecuencia_muestreo = 44100  
        canales = 1  
        ancho_muestra = 2  
        total_muestras = frecuencia_muestreo * 1 # 1 segundo de silencio
        datos_silencio = b'\x00' * (total_muestras * canales * ancho_muestra)
        
        with wave.open(nombre_archivo, 'wb') as archivo_wav:
            archivo_wav.setnchannels(canales)
            archivo_wav.setsampwidth(ancho_muestra)
            archivo_wav.setframerate(frecuencia_muestreo)
            archivo_wav.writeframes(datos_silencio)

# Inicializamos el archivo al cargar la interfaz
inicializar_archivo_wav()

# --- SÍNTESIS DE VOZ (El navegador habla) ---
def hablar_veredicto(texto_a_leer):
    js_code = f"""
    <script>
        window.speechSynthesis.cancel();
        const mensaje = new SpeechSynthesisUtterance({json.dumps(texto_a_leer)});
        mensaje.lang = 'es-MX';
        mensaje.rate = 1.0;
        mensaje.pitch = 0.9;
        window.speechSynthesis.speak(mensaje);
    </script>
    """
    components.html(js_code, height=0, width=0)

# --- ESQUEMA DEL VEREDICTO (Pydantic compatible con Strict Mode) ---
class VeredictoRap(BaseModel):
    puntuacion_total: float = Field(description="Calificación general del rap de 1 a 10")
    analisis_tecnico: str = Field(description="Crítica detallada de las rimas, métricas y estructuras")
    punchline_destacado: str = Field(description="La mejor frase o remate encontrado en el texto")
    veredicto_callejero: str = Field(description="Frase con mucha jerga y actitud de juez de rap dictando el resultado")

# --- PROCESAMIENTO CON GROQ (Whisper + GPT-OSS) ---
def procesar_batalla_audio(audio_bytes, api_key: str):
    client = Groq(api_key=api_key)
    nombre_archivo = "mi_freestyle.wav"
    
    # Escribimos los bytes de voz reales capturados por el micrófono
    with open(nombre_archivo, "wb") as f:
        f.write(audio_bytes)
    
    # 1. Transcribir el audio usando Whisper-large-v3
    with open(nombre_archivo, "rb") as file:
        transcripcion = client.audio.transcriptions.create(
            file=(nombre_archivo, file.read()),
            model="whisper-large-v3",
            language="es",
            response_format="text"
        )
        
    letra_detectada = str(transcripcion).strip()
    
    if not letra_detectada:
        letra_detectada = "[Audio vacío o no se detectaron palabras legibles]"
    
    schema_dict = VeredictoRap.model_json_schema()
    schema_dict["additionalProperties"] = False 
    
    prompt_sistema = (
        "Actúas como un juez profesional de batallas de rap (como en Red Bull o FMS). "
        "Analiza el texto provisto y genera tu veredicto adaptándote estrictamente al esquema JSON solicitado."
    )

    # Llamada al modelo con formato de esquema estricto
    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": f"Evalúa estas barras extraídas de un audio:\n\n{letra_detectada}"}
        ],
        temperature=0.7,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "VeredictoRapSchema",
                "strict": True, 
                "schema": schema_dict
            }
        }
    )
    
    contenido_respuesta = completion.choices[0].message.content
    datos_json = json.loads(contenido_respuesta)
    
    return letra_detectada, VeredictoRap(**datos_json)


# --- INTERFAZ GRÁFICA ---
st.set_page_config(page_title="IA Rap Judge - Audio Edition", page_icon="🎤", layout="wide")
st.title("🎤 IA Rap Judge (Batalla de 4 Concursantes)")
st.subheader("Graba a cada participante en una tarjeta y deja que el juez evalúe la batalla")

NUM_CONCURSANTES = 4

if "concursantes" not in st.session_state:
    st.session_state.concursantes = {
        i: {
            "nombre": f"Concursante {i + 1}",
            "audio": None,
            "letra": "",
            "resultado": None,
        }
        for i in range(NUM_CONCURSANTES)
    }

# Barra lateral
st.sidebar.header("🔑 Configuración")
api_key_input = st.sidebar.text_input(
    "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",
    type="password",
    
    key="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"
)
st.sidebar.markdown("[Consigue tu llave gratis aquí](https://groq.com)")

st.markdown("### 🎙️ Panel de grabación")

cols = st.columns(2)
for idx, col in enumerate(cols):
    with col:
        st.markdown(f"### {idx + 1}. Concursante")
        nombre = st.text_input(
            "Nombre",
            value=st.session_state.concursantes[idx]["nombre"],
            key=f"nombre_{idx}",
        )
        st.session_state.concursantes[idx]["nombre"] = nombre

        audio_rec = mic_recorder(
            start_prompt="🔴 Grabar",
            stop_prompt="⏹️ Guardar audio",
            just_once=False,
            key=f"recorder_{idx}",
        )

        if audio_rec:
            st.session_state.concursantes[idx]["audio"] = audio_rec["bytes"]

        if st.session_state.concursantes[idx]["audio"] is not None:
            st.success("Audio listo para evaluar")
        else:
            st.caption("Aún no hay audio grabado")

        st.markdown("---")

for idx in range(2, NUM_CONCURSANTES):
    col = cols[idx % 2]
    with col:
        st.markdown(f"### {idx + 1}. Concursante")
        nombre = st.text_input(
            "Nombre",
            value=st.session_state.concursantes[idx]["nombre"],
            key=f"nombre_{idx}",
        )
        st.session_state.concursantes[idx]["nombre"] = nombre

        audio_rec = mic_recorder(
            start_prompt="🔴 Grabar",
            stop_prompt="⏹️ Guardar audio",
            just_once=False,
            key=f"recorder_{idx}",
        )

        if audio_rec:
            st.session_state.concursantes[idx]["audio"] = audio_rec["bytes"]

        if st.session_state.concursantes[idx]["audio"] is not None:
            st.success("Audio listo para evaluar")
        else:
            st.caption("Aún no hay audio grabado")

        st.markdown("---")

if st.button("🔥 Lanzar veredicto de los 4 concursantes", use_container_width=True):
    if not api_key_input:
        st.error("Por favor, introduce tu API Key de Groq en la barra lateral.")
    else:
        hay_audio = False
        for idx, concursante in st.session_state.concursantes.items():
            if concursante["audio"] is not None:
                hay_audio = True
                break

        if not hay_audio:
            st.warning("No hay ningún audio registrado. ¡Graba a los participantes antes de juzgar!")
        else:
            with st.spinner("Escuchando a los cuatro participantes y preparando la crítica... 🧠"):
                for idx, concursante in st.session_state.concursantes.items():
                    if concursante["audio"] is None:
                        continue

                    try:
                        letra, resultado = procesar_batalla_audio(concursante["audio"], api_key_input)
                        st.session_state.concursantes[idx]["letra"] = letra
                        st.session_state.concursantes[idx]["resultado"] = resultado
                    except Exception as e:
                        st.session_state.concursantes[idx]["letra"] = ""
                        st.session_state.concursantes[idx]["resultado"] = None
                        st.error(f"Error al analizar a {concursante['nombre']}: {e}")

            st.success("¡Análisis completado para todos los concursantes!")

st.markdown("---")
st.markdown("### 📊 Resultados")

result_cols = st.columns(2)
for idx, col in enumerate(result_cols):
    with col:
        concursante = st.session_state.concursantes[idx]
        st.markdown(f"### {concursante['nombre']}")

        if concursante["resultado"]:
            r = concursante["resultado"]
            st.metric(label="🏆 Puntuación", value=f"{r.puntuacion_total} / 10")
            st.markdown("**Punchline detectado**")
            st.info(f'"{r.punchline_destacado}"')
            st.markdown("**Análisis técnico**")
            st.write(r.analisis_tecnico)
            st.markdown("**Veredicto del juez**")
            st.warning(r.veredicto_callejero)

            if st.button(f"🔊 Repetir veredicto - {concursante['nombre']}", key=f"repetir_{idx}"):
                texto_discurso = f"Tu puntuación es de {r.puntuacion_total}. {r.veredicto_callejero}"
                hablar_veredicto(texto_discurso)
        else:
            st.info("Aún no hay veredicto para este concursante")

for idx in range(2, NUM_CONCURSANTES):
    col = result_cols[idx % 2]
    with col:
        concursante = st.session_state.concursantes[idx]
        st.markdown(f"### {concursante['nombre']}")

        if concursante["resultado"]:
            r = concursante["resultado"]
            st.metric(label="🏆 Puntuación", value=f"{r.puntuacion_total} / 10")
            st.markdown("**Punchline detectado**")
            st.info(f'"{r.punchline_destacado}"')
            st.markdown("**Análisis técnico**")
            st.write(r.analisis_tecnico)
            st.markdown("**Veredicto del juez**")
            st.warning(r.veredicto_callejero)

            if st.button(f"🔊 Repetir veredicto - {concursante['nombre']}", key=f"repetir_{idx}"):
                texto_discurso = f"Tu puntuación es de {r.puntuacion_total}. {r.veredicto_callejero}"
                hablar_veredicto(texto_discurso)
        else:
            st.info("Aún no hay veredicto para este concursante")

