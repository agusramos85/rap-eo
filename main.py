import os
import json
import wave
import streamlit as st
from groq import Groq
from pydantic import BaseModel, Field
import streamlit.components.v1 as components
from streamlit_mic_recorder import mic_recorder

try:
    from PIL import Image
except ImportError:
    Image = None

project_dir = os.path.dirname(__file__)
root_logo_path = os.path.join(project_dir, "logo.png")
build_logo_path = os.path.join(project_dir, "build", "flutter", "images", "logo.png")
logo_path = root_logo_path if os.path.exists(root_logo_path) else build_logo_path
favicon_path = os.path.join(project_dir, "favicon.png")


def generate_favicon(source_path, target_path):
    if Image is None:
        return False
    try:
        img = Image.open(source_path).convert("RGBA")
        img.thumbnail((64, 64), Image.LANCZOS)
        favicon = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
        favicon.paste(img, ((64 - img.width) // 2, (64 - img.height) // 2), img)
        favicon.save(target_path, format="PNG")
        return True
    except Exception:
        return False

if os.path.exists(logo_path) and not os.path.exists(favicon_path):
    generate_favicon(logo_path, favicon_path)

page_icon_path = favicon_path if os.path.exists(favicon_path) else (logo_path if os.path.exists(logo_path) else "🎤")

# Configuración de la página
st.set_page_config(page_title="JUECES Y VERDUGOS DE TU RRUMBO", page_icon=page_icon_path)

if os.path.exists(logo_path):
    st.image(logo_path, width=180)

brand_css_path = os.path.join(project_dir, "brand_styles.css")
if os.path.exists(brand_css_path):
    with open(brand_css_path, "r", encoding="utf-8") as f:
        brand_css = f.read()
    st.markdown(f"<style>{brand_css}</style>", unsafe_allow_html=True)
else:
    st.warning("una autoopsia a tu style")

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Acceso requerido")
    with st.form("login_form"):
        usuario = st.text_input("Usuario")
        password = st.text_input("Contraseña", type="password")
        enviado = st.form_submit_button("Entrar")

        if enviado:
            if usuario == "admin" and password == "rapReich":
                st.session_state.autenticado = True
                st.success("Acceso concedido")
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos")
    st.stop()

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
st.title("OMERTA AI. - JURADO")
st.subheader("El juez está listo para escuchar tu freestyle")

# Barra lateral
st.sidebar.header("🔑 OMERTA IA 7")
num_concursantes = st.sidebar.number_input(
    "Número de concursantes",
    min_value=1,
    max_value=8,
    value=st.session_state.get("num_concursantes", 4),
    step=1,
    key="num_concursantes_input",
)
num_concursantes = int(num_concursantes)
st.session_state.num_concursantes = num_concursantes

if "concursantes" not in st.session_state or len(st.session_state.concursantes) != num_concursantes:
    concursantes_actualizados = {}
    for i in range(num_concursantes):
        if "concursantes" in st.session_state and i in st.session_state.concursantes:
            anterior = st.session_state.concursantes[i]
            audios_existentes = anterior.get("audios")
            if audios_existentes is None:
                audios_existentes = [anterior.get("audio")] + [None] * 3
            audios_existentes = list(audios_existentes)[:4] + [None] * max(0, 4 - len(audios_existentes))
            concursantes_actualizados[i] = {
                "nombre": anterior.get("nombre", f"Concursante {i + 1}"),
                "audios": audios_existentes,
                "letra": anterior.get("letra", ""),
                "resultado": anterior.get("resultado"),
            }
        else:
            concursantes_actualizados[i] = {
                "nombre": f"Concursante {i + 1}",
                "audios": [None, None, None, None],
                "letra": "",
                "resultado": None,
            }
    st.session_state.concursantes = concursantes_actualizados

api_key_input = st.sidebar.text_input(
    "API Key",
    value='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',
    type="password",
    key="groq_api_key",
)
st.sidebar.markdown("[Consigue tu llave gratis aquí](https://groq.com)")

st.markdown("### 🎙️ Panel de grabación")

cols = st.columns(2)
for idx in range(st.session_state.num_concursantes):
    col = cols[idx % 2]
    with col:
        st.markdown('<div class="brand-card">', unsafe_allow_html=True)
        st.markdown(f"### {idx + 1}. Concursante")
        nombre = st.text_input(
            "Nombre",
            value=st.session_state.concursantes[idx]["nombre"],
            key=f"nombre_{idx}",
        )
        st.session_state.concursantes[idx]["nombre"] = nombre

        audios_list = st.session_state.concursantes[idx].get("audios", [None, None, None, None])
        for rec_slot in range(4):
            audio_rec = mic_recorder(
                start_prompt=f"🔴 Grabar {rec_slot + 1}",
                stop_prompt="⏹️ Guardar grabación",
                just_once=False,
                key=f"recorder_{idx}_{rec_slot}",
            )
            if audio_rec:
                audios_list[rec_slot] = audio_rec["bytes"]

        st.session_state.concursantes[idx]["audios"] = audios_list

        num_audios = sum(1 for a in audios_list if a is not None)
        if num_audios > 0:
            st.success(f"Grabaciones listas: {num_audios} / 4")
        else:
            st.caption("Aún no hay grabaciones")

        st.markdown("---")
        st.markdown('</div>', unsafe_allow_html=True)

if st.button("🔥 Lanzar veredicto de los 4 concursantes", use_container_width=True):
    if not api_key_input:
        st.error("Por favor, introduce tu API Key de Groq en la barra lateral.")
    else:
        hay_audio = False
        for idx, concursante in st.session_state.concursantes.items():
            if any(a is not None for a in concursante.get("audios", [])):
                hay_audio = True
                break

        if not hay_audio:
            st.warning("No hay ningún audio registrado. ¡Graba a los participantes antes de juzgar!")
        else:
            with st.spinner("Escuchando a los cuatro participantes y preparando la crítica... 🧠"):
                for idx, concursante in st.session_state.concursantes.items():
                    audios = concursante.get("audios", [])
                    participante_audio = next((a for a in audios if a is not None), None)
                    if participante_audio is None:
                        continue

                    try:
                        letra, resultado = procesar_batalla_audio(participante_audio, api_key_input)
                        st.session_state.concursantes[idx]["letra"] = letra
                        st.session_state.concursantes[idx]["resultado"] = resultado
                    except Exception as e:
                        st.error(f"Error al analizar a {concursante['nombre']}: {e}")

            st.success("¡Análisis completado para todos los concursantes!")

st.markdown("---")
st.markdown("### 📊 Resultados")

result_cols = st.columns(2)
for idx in range(st.session_state.num_concursantes):
    col = result_cols[idx % 2]
    with col:
        st.markdown('<div class="brand-card">', unsafe_allow_html=True)
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
        st.markdown('</div>', unsafe_allow_html=True)

