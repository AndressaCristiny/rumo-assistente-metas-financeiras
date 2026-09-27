"""
Rumo — assistente de planejamento de metas financeiras.
Interface Streamlit + LLM local via Ollama.

Execução:
    ollama serve
    ollama pull llama3.2
    streamlit run src/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from contexto import bloco_de_fatos, montar_prompt          # noqa: E402
from motor import brl, levantar_fatos                        # noqa: E402

OLLAMA_URL = "http://localhost:11434"
MODELO = "llama3.2"
TIMEOUT = 180

st.set_page_config(page_title="Rumo — metas financeiras", page_icon="🧭", layout="wide")


# --------------------------------------------------------------------------- #
# LLM
# --------------------------------------------------------------------------- #

def ollama_disponivel() -> tuple[bool, str]:
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3)
        r.raise_for_status()
        modelos = [m["name"] for m in r.json().get("models", [])]
        if not modelos:
            return False, "O Ollama está rodando, mas nenhum modelo foi baixado. Rode: ollama pull llama3.2"
        if not any(m.split(":")[0] == MODELO.split(":")[0] for m in modelos):
            return False, f"O modelo {MODELO} não está instalado. Disponíveis: {', '.join(modelos)}"
        return True, f"Ollama conectado — modelo {MODELO}"
    except requests.exceptions.RequestException:
        return False, "Ollama não está rodando. Abra um terminal e rode: ollama serve"


def perguntar(pergunta: str, historico: list[dict]) -> str:
    resposta = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": MODELO,
            "prompt": montar_prompt(pergunta, historico),
            "stream": False,
            # Temperatura baixa: aqui não se quer criatividade, se quer fidelidade aos fatos.
            "options": {"temperature": 0.2, "num_ctx": 8192},
        },
        timeout=TIMEOUT,
    )
    resposta.raise_for_status()
    return resposta.json()["response"].strip()


# --------------------------------------------------------------------------- #
# Barra lateral — o painel de fatos
# --------------------------------------------------------------------------- #

fatos = levantar_fatos()

with st.sidebar:
    st.header("Painel do cliente")
    st.caption(
        "Tudo aqui foi calculado em Python, não pelo modelo. "
        "É exatamente o que o Rumo recebe como fonte de números."
    )

    c, o = fatos["cliente"], fatos["orcamento"]
    st.subheader(c["nome"])
    st.write(f"{c['idade']} anos · perfil {c['perfil_investidor']}")

    col1, col2 = st.columns(2)
    col1.metric("Receita média", brl(o["receita_media"]))
    col2.metric("Despesa média", brl(o["despesa_media"]))
    st.metric("Sobra média por mês", brl(o["sobra_media"]),
              f"{o['taxa_poupanca']*100:.1f}% da receita")

    st.divider()
    st.subheader("Metas")
    for m in fatos["metas"]:
        st.write(f"**{m['nome']}**")
        st.progress(min(m["progresso"], 1.0),
                    text=f"{brl(m['valor_atual'])} de {brl(m['valor_necessario'])}")
        st.caption(
            f"Faltam {brl(m['falta'])} em {m['meses_restantes']} meses · "
            f"aporte de {brl(m['aporte_necessario'])}/mês"
        )

    cf = fatos["conflito"]
    st.divider()
    if cf["cabe_tudo"]:
        st.success(f"As metas cabem juntas na sobra de {brl(cf['sobra_media'])}.")
    else:
        st.warning(
            f"As duas metas somam {brl(cf['aporte_total_necessario'])} por mês, "
            f"mas a sobra é {brl(cf['sobra_media'])}. Faltam {brl(cf['deficit'])}."
        )

    with st.expander("Ver o bloco de fatos enviado ao modelo"):
        st.code(bloco_de_fatos(fatos), language="text")


# --------------------------------------------------------------------------- #
# Conversa
# --------------------------------------------------------------------------- #

st.title("🧭 Rumo")
st.caption("Assistente de planejamento de metas financeiras — o modelo explica, o Python calcula.")

ok, recado = ollama_disponivel()
(st.success if ok else st.error)(recado)
if not ok:
    st.info(
        "O Rumo precisa de um modelo local para redigir as respostas. "
        "A camada de cálculo, no painel ao lado, funciona sem ele — e é ela que "
        "produz todos os números."
    )

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

if not st.session_state.mensagens:
    st.write("**Experimente perguntar:**")
    for sugestao in [
        "Consigo bater as duas metas no prazo?",
        "Quanto preciso guardar por mês para a reserva de emergência?",
        "Onde estou gastando mais?",
        "Qual produto é melhor para a reserva?",
    ]:
        st.markdown(f"- {sugestao}")

for msg in st.session_state.mensagens:
    st.chat_message(msg["role"]).write(msg["content"])

if pergunta := st.chat_input("Sua dúvida sobre as metas..." if ok else "Inicie o Ollama para conversar",
                             disabled=not ok):
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    st.chat_message("user").write(pergunta)

    with st.chat_message("assistant"), st.spinner("Consultando os fatos..."):
        try:
            resposta = perguntar(pergunta, st.session_state.mensagens[:-1])
        except requests.exceptions.Timeout:
            resposta = "O modelo demorou demais para responder. Tente de novo ou use um modelo menor."
        except requests.exceptions.RequestException as erro:
            resposta = f"Não consegui falar com o Ollama: {erro}"
        st.write(resposta)

    st.session_state.mensagens.append({"role": "assistant", "content": resposta})
