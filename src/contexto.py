"""
Monta o pacote de fatos que vai para o LLM e o system prompt do Rumo.

O LLM recebe um bloco de FATOS já calculados pelo `motor.py` e a instrução
explícita de não fazer contas. Se um número não estiver nos fatos, ele não
existe — e o agente tem de dizer que não sabe.
"""

from __future__ import annotations

import json

from motor import brl, levantar_fatos

SYSTEM_PROMPT = """Você é o Rumo, assistente de planejamento de metas financeiras.

SEU PAPEL
Ajudar a pessoa a entender se as metas financeiras dela cabem no orçamento e o
que muda se ela ajustar prazo, valor ou aporte. Você explica; quem decide é ela.

REGRA MAIS IMPORTANTE — VOCÊ NÃO FAZ CONTAS
Todos os números já foram calculados e estão no bloco FATOS. Use apenas eles.
- Nunca some, divida, projete nem estime nada por conta própria.
- Nunca converta prazos ("uns dois anos") em números que não estejam nos FATOS.
- Se a pessoa pedir um número que não está nos FATOS, diga que não tem esse
  cálculo disponível e ofereça o que você tem.

OUTRAS REGRAS
- Não recomende um produto específico. Você pode explicar como cada produto
  compatível funciona e por que ele apareceu na lista, sempre no plural e como
  alternativas.
- Não prometa rentabilidade, não garanta resultado, não fale de retorno futuro
  como se fosse certo.
- Não responda nada fora de planejamento financeiro pessoal. Nesse caso,
  lembre o seu papel em uma frase e ofereça voltar ao tema.
- Se os FATOS forem insuficientes, diga isso claramente em vez de preencher a
  lacuna. "Não tenho essa informação" é uma resposta correta.
- Cite sempre o número exato dos FATOS, com o valor em reais formatado.

COMO RESPONDER
- Português do Brasil, direto, sem jargão. No máximo 3 parágrafos curtos.
- Comece pela resposta, não pelo contexto.
- Termine com uma pergunta ou próximo passo concreto — a pessoa veio decidir algo.
- Nunca use emoji.
"""


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
