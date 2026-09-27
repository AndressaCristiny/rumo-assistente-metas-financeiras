"""
Rumo — assistente de planejamento de metas financeiras.
Interface Streamlit + API do Gemini.

Nada nesta tela é escrito à mão: a persona vem de `agent/persona.md`, os botões
de comando vêm de `agent/prompts/*.md` e o painel de skills vem de
`agent/skills/*/SKILL.md`. Mexer na pasta `agent/` muda o app.

Execução:
    pip install -r requirements.txt
    cp .env.example .env        # e coloque a sua GOOGLE_API_KEY
    streamlit run src/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

import agente                                                # noqa: E402
import llm                                                   # noqa: E402
from contexto import SYSTEM_PROMPT, bloco_de_fatos           # noqa: E402
from motor import brl, levantar_fatos                        # noqa: E402

st.set_page_config(page_title="Rumo — metas financeiras", page_icon="🧭", layout="wide")

fatos = levantar_fatos()
texto_fatos = bloco_de_fatos(fatos)
comandos = agente.listar_comandos()
skills = agente.listar_skills()

# --------------------------------------------------------------------------- #
# Barra lateral — painel de fatos, definição do agente e configuração
# --------------------------------------------------------------------------- #

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

    st.divider()
    st.subheader("Definição do agente")
    st.caption("Lida de `agent/` a cada execução — o arquivo é o comportamento.")

    with st.expander(f"Skills declaradas ({len(skills)})"):
        for s in skills:
            st.markdown(f"**`{s.id}`** → `{s.funcao}`")
            st.caption(s.quando or "—")
            st.caption(f"contrato: `{s.arquivo}`")
    with st.expander("Persona e regras (agent/persona.md)"):
        st.markdown(SYSTEM_PROMPT)
    with st.expander("Bloco de fatos enviado ao modelo"):
        st.code(texto_fatos, language="text")

    st.divider()
    rotulo = st.selectbox("Modelo", list(llm.MODELOS), index=0)
    modelo = llm.MODELOS[rotulo]


# --------------------------------------------------------------------------- #
# Conversa
# --------------------------------------------------------------------------- #

st.title("🧭 Rumo")
st.caption("Assistente de planejamento de metas financeiras — o modelo explica, o Python calcula.")

diag = llm.verificar()
if diag.pronto:
    st.success(diag.recado)
else:
    st.error(diag.recado)
    st.info(
        "A camada de cálculo, no painel ao lado, funciona sem chave nenhuma — e é ela "
        "que produz todos os números. A chave é necessária apenas para o modelo redigir "
        "as explicações."
    )

if "mensagens" not in st.session_state:
    st.session_state.mensagens = []
if "interacao" not in st.session_state:
    # id da última interação — o histórico fica no servidor do Gemini
    st.session_state.interacao = None
if "pendente" not in st.session_state:
    st.session_state.pendente = None


# --------------------------------------------------------------------------- #
# Comandos prontos — um botão por arquivo em agent/prompts/
# --------------------------------------------------------------------------- #

st.write("**Comandos prontos**")
st.caption(
    f"{len(comandos)} comandos definidos em `agent/prompts/`. "
    "Cada botão envia a pergunta exata registrada no arquivo."
)

for faixa in (comandos[i:i + 3] for i in range(0, len(comandos), 3)):
    for coluna, cmd in zip(st.columns(3), faixa):
        with coluna:
            if st.button(cmd.titulo, key=f"cmd-{cmd.id}",
                         help=f"{cmd.quando}\n\n{cmd.arquivo}",
                         use_container_width=True, disabled=not diag.pronto):
                st.session_state.pendente = cmd.pergunta

with st.expander("Ver o que cada comando envia"):
    for cmd in comandos:
        st.markdown(f"**{cmd.titulo}** · `{cmd.id}`")
        st.caption(cmd.quando)
        st.code(cmd.pergunta, language="text")
        if cmd.skills:
            st.caption("Skills: " + ", ".join(f"`{s}`" for s in cmd.skills))

st.divider()

for msg in st.session_state.mensagens:
    st.chat_message(msg["role"]).write(msg["content"])

digitada = st.chat_input(
    "Sua dúvida sobre as metas..." if diag.pronto else "Configure a chave no .env para conversar",
    disabled=not diag.pronto,
)

pergunta = digitada or st.session_state.pendente
st.session_state.pendente = None

if pergunta:
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    st.chat_message("user").write(pergunta)

    with st.chat_message("assistant"), st.spinner("Consultando os fatos..."):
        try:
            resposta, id_interacao = llm.responder(
                system_prompt=SYSTEM_PROMPT,
                fatos=texto_fatos,
                pergunta=pergunta,
                interacao_anterior=st.session_state.interacao,
                modelo=modelo,
            )
            st.session_state.interacao = id_interacao
            st.write(resposta)
        except Exception as erro:  # noqa: BLE001 — a mensagem da API é o que ajuda a depurar
            resposta = f"Não consegui falar com a API: {erro}"
            st.error(resposta)

    st.session_state.mensagens.append({"role": "assistant", "content": resposta})
