
#############################
# Agente Economico          #
# Interfaz con Streamlit    #
#############################
# Ejecutar con:  streamlit run economic_agent_streamlit.py

from dotenv import load_dotenv
from groq import Groq
import os
import json
from datetime import datetime
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from basic_memory import BasicMemory
from economic_tools import EconomicTools


# ---------------------------------------------------------------
# Configuracion general (puedes cambiar el nombre del agente aqui)
# ---------------------------------------------------------------
AGENT_NAME = "Quetzal IA"
AGENT_SUBTITLE = "Tu asistente económico de confianza"
MEMORY_MAX_MESSAGES = 10

st.set_page_config(page_title=AGENT_NAME, page_icon="🦜", layout="wide")

# ---------------------------------------------------------------
# API key: en la computadora se lee del archivo .env;
# en internet se lee de los Secrets de Streamlit Cloud
# ---------------------------------------------------------------
load_dotenv()
api_key = os.environ.get("GROQ_API_KEY")
if not api_key:
    try:
        api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        api_key = None

if not api_key:
    st.error("No se encontró la GROQ_API_KEY. Configúrala en el archivo .env o en los Secrets de Streamlit.")
    st.stop()

client = Groq(api_key=api_key)

now = datetime.now(ZoneInfo("America/Guatemala"))


SYSTEM_PROMPT = f"""
Eres {AGENT_NAME}, un agente economico que habla en español y responde de forma clara, breve y profesional.
La fecha actual es {now.strftime('%d/%m/%Y')}.

Objetivo:
Analizar el entorno macroeconomico y cambiario de un pais para apoyar decisiones de
comercio exterior e inversion. Siempre que sea posible, responde con datos obtenidos
de tus herramientas e indica el año o la fecha de los datos.

Herramientas:
- consultar_tipo_cambio_api: tipo de cambio actual entre dos monedas (por defecto hacia GTQ).
- consultar_indicador_banco_mundial: inflacion, pib, crecimiento_pib, desempleo o remesas de un pais.
  El pais se envia con su codigo ISO de 3 letras (Guatemala = GTM, Mexico = MEX, Estados Unidos = USA).
- consultar_precio_cripto: precio actual en USD de una criptomoneda (ejemplo: bitcoin, ethereum).
- consultar_info_pais: capital, poblacion, region, nivel de ingreso y codigos ISO de un pais.
- consultar_feriados: feriados oficiales de un pais en un año. El pais se envia con su
  codigo ISO de 2 letras (Guatemala = GT).

Reglas:
- Si no conoces el codigo del pais, usa primero consultar_info_pais.
- Puedes usar varias herramientas en una misma respuesta si la pregunta lo requiere.
- Si una herramienta devuelve error, informalo al usuario sin inventar datos.
- Cuando consultes indicadores del Banco Mundial, la interfaz mostrara una grafica automaticamente;
  puedes mencionarlo, pero no dibujes tablas ASCII ni graficas en texto.
- Solo respondes temas economicos; si te preguntan otra cosa, indicalo amablemente.
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "consultar_tipo_cambio_api",
            "description": "Consulta el tipo de cambio actual de una moneda hacia otra moneda.",
            "parameters": {
                "type": "object",
                "properties": {
                    "moneda": {"type": "string", "description": "Codigo de la moneda de origen, por ejemplo USD"},
                    "moneda_destino": {"type": "string", "description": "Codigo de la moneda de destino, por defecto GTQ"}
                },
                "required": ["moneda"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_indicador_banco_mundial",
            "description": "Consulta los datos mas recientes de un indicador macroeconomico de un pais segun el Banco Mundial.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pais": {"type": "string", "description": "Codigo ISO de 3 letras del pais, por ejemplo GTM"},
                    "indicador": {
                        "type": "string",
                        "enum": ["inflacion", "pib", "crecimiento_pib", "desempleo", "remesas"],
                        "description": "Indicador a consultar"
                    }
                },
                "required": ["pais", "indicador"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_precio_cripto",
            "description": "Consulta el precio actual en USD y la variacion de 24 horas de una criptomoneda.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cripto": {"type": "string", "description": "Nombre de la criptomoneda en ingles y minusculas, por ejemplo bitcoin"}
                },
                "required": ["cripto"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_info_pais",
            "description": "Obtiene capital, poblacion, region, nivel de ingreso y codigos ISO de un pais.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pais": {"type": "string", "description": "Nombre del pais en español, por ejemplo Guatemala"}
                },
                "required": ["pais"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_feriados",
            "description": "Obtiene los feriados oficiales de un pais en un año determinado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "codigo_pais": {"type": "string", "description": "Codigo ISO de 2 letras del pais, por ejemplo GT"},
                    "anio": {"type": "integer", "description": "Año a consultar, por ejemplo 2026"}
                },
                "required": ["codigo_pais", "anio"]
            }
        }
    }
]


# ---------------------------------------------------------------
# Logica del agente
# ---------------------------------------------------------------
def ejecutar_herramienta(name: str, args: dict):
    tools = EconomicTools()

    if name == "consultar_tipo_cambio_api":
        return tools.consultar_tipo_cambio_api(
            moneda=args.get("moneda"),
            moneda_destino=args.get("moneda_destino", "GTQ")
        )
    elif name == "consultar_indicador_banco_mundial":
        return tools.consultar_indicador_banco_mundial(
            pais=args.get("pais"),
            indicador=args.get("indicador")
        )
    elif name == "consultar_precio_cripto":
        return tools.consultar_precio_cripto(cripto=args.get("cripto"))
    elif name == "consultar_info_pais":
        return tools.consultar_info_pais(pais=args.get("pais"))
    elif name == "consultar_feriados":
        return tools.consultar_feriados(
            codigo_pais=args.get("codigo_pais"),
            anio=args.get("anio")
        )
    else:
        return {"error": f"Herramienta desconocida: {name}"}


def process_response(client: Groq, memory_messages: list[dict], user_text: str):
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(memory_messages)
    messages.append({"role": "user", "content": user_text})

    herramientas_usadas = []
    datos_grafica = []

    while True:
        resp = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            tools=TOOLS
        )

        msg = resp.choices[0].message

        if not getattr(msg, "tool_calls", None):
            return msg.content or "", herramientas_usadas, datos_grafica

        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [tc.model_dump() for tc in msg.tool_calls]
        })

        for tool_call in msg.tool_calls:
            name = tool_call.function.name
            args = json.loads(tool_call.function.arguments or "{}")
            result = ejecutar_herramienta(name, args)

            herramientas_usadas.append(name)
            if name == "consultar_indicador_banco_mundial" and isinstance(result, dict):
                datos_grafica.append(result)

            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False)
            })


# ---------------------------------------------------------------
# Graficas
# ---------------------------------------------------------------
def mostrar_graficas(datos: list[dict]):
    if not datos:
        return

    filas = []
    for d in datos:
        for v in d.get("valores", []):
            if v.get("valor") is not None:
                filas.append({
                    "Indicador": d.get("indicador"),
                    "País": d.get("pais"),
                    "Año": str(v.get("anio")),
                    "Valor": round(float(v.get("valor")), 2),
                })
    if not filas:
        return

    df = pd.DataFrame(filas)
    for indicador, grupo in df.groupby("Indicador"):
        tabla = grupo.pivot_table(index="Año", columns="País", values="Valor").sort_index()
        with st.container(border=True):
            st.markdown(f"**{indicador}**")
            if tabla.shape[1] == 1:
                st.bar_chart(tabla)
            else:
                st.line_chart(tabla)
            st.caption("Fuente: Banco Mundial (datos más recientes disponibles).")


# ---------------------------------------------------------------
# Estado de la sesion
# ---------------------------------------------------------------
if "memory" not in st.session_state:
    st.session_state.memory = BasicMemory(max_messages=MEMORY_MAX_MESSAGES)
if "chat" not in st.session_state:
    st.session_state.chat = []


# ---------------------------------------------------------------
# Estilos
# ---------------------------------------------------------------
st.markdown("""
<style>
    .block-container { padding-top: 2rem; }
    .subtitulo { color: #6b7280; font-size: 0.9rem; margin-top: -0.6rem; }
    .hora { color: #9ca3af; font-size: 0.75rem; text-align: right; }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------------
# Barra lateral
# ---------------------------------------------------------------
with st.sidebar:
    with st.container(border=True):
        st.markdown(f"### 🦜 {AGENT_NAME}")
        st.markdown(f"<p class='subtitulo'>{AGENT_SUBTITLE}</p>", unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("**💡 ¿Qué puedo hacer?**")
        st.caption(
            "Analizo el entorno macroeconómico y cambiario de un país para apoyar "
            "decisiones de comercio exterior e inversión."
        )

    with st.container(border=True):
        st.markdown("**📊 Herramientas incluidas**")
        st.markdown(
            "- 💱 Tipo de cambio\n"
            "- 🏦 Indicadores del Banco Mundial\n"
            "- ₿ Precio de criptomonedas\n"
            "- 🌎 Perfil económico de países\n"
            "- 📅 Feriados oficiales"
        )

    with st.container(border=True):
        st.markdown("**🧠 Memoria**")
        st.caption(f"Recuerdo los últimos {MEMORY_MAX_MESSAGES} mensajes de la conversación.")

    if st.button("🗑️ Nueva conversación", use_container_width=True):
        st.session_state.memory = BasicMemory(max_messages=MEMORY_MAX_MESSAGES)
        st.session_state.chat = []
        st.rerun()


# ---------------------------------------------------------------
# Area principal: chat
# ---------------------------------------------------------------
st.markdown("### 💬 Conversación con el agente")

if not st.session_state.chat:
    st.info(
        "Prueba con: *¿Cuál ha sido la inflación de Guatemala en los últimos años?* · "
        "*¿A cuánto está el dólar?* · "
        "*Compara el crecimiento del PIB de Guatemala y México*"
    )

AVATARES = {"user": "👤", "assistant": "🦜"}

for m in st.session_state.chat:
    with st.chat_message(m["role"], avatar=AVATARES[m["role"]]):
        st.markdown(m["content"])
        if m.get("charts"):
            mostrar_graficas(m["charts"])
        if m.get("tools"):
            st.caption("🔧 Herramientas usadas: " + ", ".join(dict.fromkeys(m["tools"])))
        st.markdown(f"<div class='hora'>{m['time']}</div>", unsafe_allow_html=True)

user_text = st.chat_input("Escribe tu pregunta o solicitud...")

if user_text:
    hora = datetime.now(ZoneInfo("America/Guatemala")).strftime("%H:%M")
    st.session_state.chat.append({"role": "user", "content": user_text, "time": hora})
    with st.chat_message("user", avatar=AVATARES["user"]):
        st.markdown(user_text)
        st.markdown(f"<div class='hora'>{hora}</div>", unsafe_allow_html=True)

    with st.chat_message("assistant", avatar=AVATARES["assistant"]):
        with st.spinner("Analizando..."):
            try:
                respuesta, usadas, graficas = process_response(
                    client, st.session_state.memory.messages(), user_text
                )
            except Exception as e:
                respuesta, usadas, graficas = f"⚠️ Ocurrió un error al consultar el modelo: {e}", [], []

        hora = datetime.now(ZoneInfo("America/Guatemala")).strftime("%H:%M")
        st.markdown(respuesta)
        mostrar_graficas(graficas)
        if usadas:
            st.caption("🔧 Herramientas usadas: " + ", ".join(dict.fromkeys(usadas)))
        st.markdown(f"<div class='hora'>{hora}</div>", unsafe_allow_html=True)

    st.session_state.chat.append({
        "role": "assistant", "content": respuesta,
        "tools": usadas, "charts": graficas, "time": hora
    })

    st.session_state.memory.add("user", user_text)
    st.session_state.memory.add("assistant", respuesta)