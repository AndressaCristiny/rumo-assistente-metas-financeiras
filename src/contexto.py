"""
Monta o pacote de fatos que vai para o LLM e junta tudo no prompt final.

Duas fontes, cada uma com um dono:

- a identidade do agente vem de `agent/persona.md`, lida por `agente.py`.
  Nenhuma linha do system prompt mora neste arquivo — editar a persona é
  editar o markdown, e o comportamento acompanha na hora;
- os números vêm de `motor.py`, já calculados, no bloco FATOS.

O LLM recebe os FATOS e a instrução explícita de não fazer contas. Se um número
não estiver nos fatos, ele não existe — e o agente tem de dizer que não sabe.
"""

from __future__ import annotations

import json

from agente import carregar_persona
from motor import brl, levantar_fatos

# Lido de agent/persona.md na importação: se o arquivo faltar, o erro aparece ao
# subir o app, não no meio de uma conversa.
SYSTEM_PROMPT = carregar_persona()


def bloco_de_fatos(fatos: dict | None = None) -> str:
    """Transforma os fatos calculados em texto legível para o LLM."""
    f = fatos or levantar_fatos()
    c, o, cf = f["cliente"], f["orcamento"], f["conflito"]

    linhas = [
        f"DATA DE REFERÊNCIA: {f['data_referencia']}",
        "",
        "CLIENTE",
        f"- Nome: {c['nome']}, {c['idade']} anos",
        f"- Perfil de investidor: {c['perfil_investidor']} | aceita risco: {'sim' if c['aceita_risco'] else 'não'}",
        f"- Renda mensal: {brl(c['renda_mensal'])}",
        "",
        f"ORÇAMENTO (média de {o['meses']} meses de extrato)",
        f"- Receita média: {brl(o['receita_media'])}",
        f"- Despesa média: {brl(o['despesa_media'])}",
        f"- Sobra média: {brl(o['sobra_media'])} ({o['taxa_poupanca']*100:.1f}% da receita)",
        f"- Sobra por mês: " + ", ".join(f"{k} = {brl(v)}" for k, v in o["sobra_por_mes"].items()),
        f"- Melhor mês: {o['mes_melhor']} | pior mês: {o['mes_pior']}",
        "- Despesa média por categoria: " + ", ".join(
            f"{k} = {brl(v)}" for k, v in o["despesa_por_categoria"].items()
        ),
        "",
        "METAS",
    ]

    for m in f["metas"]:
        compat = f["produtos_por_meta"].get(m["id"], [])
        linhas += [
            f"* {m['nome']} (id: {m['id']})",
            f"  - Objetivo: {brl(m['valor_necessario'])} | já guardado: {brl(m['valor_atual'])} "
            f"| falta: {brl(m['falta'])} | progresso: {m['progresso']*100:.1f}%",
            f"  - Prazo desejado: {m['prazo']} ({m['meses_restantes']} meses a partir da data de referência)",
            f"  - Aporte necessário: {brl(m['aporte_necessario'])} por mês",
            f"  - Cabe na sobra média sozinha: {'sim' if m['viavel'] else 'não'} "
            f"| folga: {brl(m['folga'])}",
            f"  - Prazo no ritmo atual (usando toda a sobra): {m['prazo_realista']}",
            f"  - Diagnóstico: {m['diagnostico']}",
            f"  - Produtos compatíveis com esta meta: {', '.join(compat) if compat else 'nenhum'}",
        ]

    linhas += [
        "",
        "AS DUAS METAS JUNTAS (competem pela mesma sobra)",
        f"- Soma dos aportes necessários: {brl(cf['aporte_total_necessario'])}",
        f"- Sobra média disponível: {brl(cf['sobra_media'])}",
        f"- As duas cabem ao mesmo tempo: {'sim' if cf['cabe_tudo'] else 'NÃO'}",
        f"- Déficit mensal: {brl(cf['deficit'])}",
        "",
        "CATÁLOGO DE PRODUTOS",
        json.dumps(f["produtos"], ensure_ascii=False, indent=2),
        "",
        "ATENDIMENTOS ANTERIORES",
        json.dumps(f["atendimentos"], ensure_ascii=False, indent=2),
    ]

    return "\n".join(linhas)


def montar_prompt(pergunta: str, historico_chat: list[dict] | None = None) -> str:
    partes = [SYSTEM_PROMPT, "", "=" * 60, "FATOS (única fonte de números permitida)", "=" * 60,
              bloco_de_fatos()]

    if historico_chat:
        partes += ["", "=" * 60, "CONVERSA ATÉ AQUI", "=" * 60]
        for msg in historico_chat[-6:]:
            papel = "Pessoa" if msg["role"] == "user" else "Rumo"
            partes.append(f"{papel}: {msg['content']}")

    partes += ["", "=" * 60, f"Pergunta: {pergunta}", "", "Resposta do Rumo:"]
    return "\n".join(partes)


if __name__ == "__main__":
    print(bloco_de_fatos())
