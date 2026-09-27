"""
Avaliação automatizada do Rumo — roda sem LLM e sem rede.

Por que isso existe: num agente de IA, a parte que dá errado em silêncio é o
número. Como no Rumo todo número vem do `motor.py`, dá para testar a parte
perigosa de forma determinística, e sobra para a avaliação humana só o que é
realmente subjetivo — o texto.

Uso:
    python avaliacao/avaliar.py            # relatório no terminal
    python avaliacao/avaliar.py --md       # relatório em markdown
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

from contexto import bloco_de_fatos                                   # noqa: E402
from motor import analisar_metas, carregar, levantar_fatos, produtos_compativeis, analisar_orcamento  # noqa: E402

CASOS = json.loads((Path(__file__).parent / "casos.json").read_text(encoding="utf-8"))
TOL = 0.01


def buscar(fatos: dict, caminho: str):
    """Resolve caminhos do tipo 'metas.reserva.falta' ou 'orcamento.sobra_media'."""
    partes = caminho.split(".")
    if partes[0] == "metas":
        meta = next(m for m in fatos["metas"] if m["id"] == partes[1])
        return meta[partes[2]]
    if caminho == "orcamento.maior_categoria":
        return max(fatos["orcamento"]["despesa_por_categoria"].items(), key=lambda kv: kv[1])[0]
    no = fatos
    for p in partes:
        no = no[p]
    return no


def bloco_calculo(fatos):
    res = []
    for c in CASOS["calculo"]:
        obtido = buscar(fatos, c["caminho"])
        ok = (abs(float(obtido) - float(c["esperado"])) <= TOL
              if isinstance(c["esperado"], (int, float)) else obtido == c["esperado"])
        res.append({**c, "obtido": obtido, "ok": ok})
    return res


def bloco_consistencia(fatos):
    metas, o, cf = fatos["metas"], fatos["orcamento"], fatos["conflito"]
    checa = {
        "K1": all(abs(m["falta"] - (m["valor_necessario"] - m["valor_atual"])) <= TOL for m in metas),
        "K2": all(abs(m["aporte_necessario"] * m["meses_restantes"] - m["falta"]) <= 1.0
                  for m in metas if m["meses_restantes"] > 0),
        "K3": abs(sum(m["aporte_necessario"] for m in metas if m["falta"] > 0)
                  - cf["aporte_total_necessario"]) <= TOL,
        "K4": (cf["deficit"] > 0) == (not cf["cabe_tudo"]),
        "K5": abs(o["sobra_media"] - (o["receita_media"] - o["despesa_media"])) <= TOL,
        "K6": all(m["viavel"] == (m["aporte_necessario"] <= o["sobra_media"]) for m in metas),
    }
    return [{**c, "ok": checa[c["id"]]} for c in CASOS["consistencia"]]


def bloco_produtos(fatos):
    perfil, produtos, transacoes, _ = carregar()
    orc = analisar_orcamento(transacoes)
    metas = analisar_metas(perfil, orc)
    risco = {p["nome"]: p["risco"] for p in produtos}
    minimo = {p["nome"]: p["aporte_minimo"] for p in produtos}
    compat = {m.id: [p["nome"] for p in produtos_compativeis(produtos, perfil, m)] for m in metas}

    checa = {
        "P1": (not perfil["aceita_risco"]) and all(
            risco[n] == "baixo" for nomes in compat.values() for n in nomes),
        "P2": all(risco[n] == "baixo" for m in metas if m.meses_restantes < 24 for n in compat[m.id]),
        "P3": all(minimo[n] <= m.aporte_necessario for m in metas for n in compat[m.id]),
        "P4": all(len(compat[m.id]) >= 1 for m in metas),
    }
    return [{**c, "ok": checa[c["id"]]} for c in CASOS["regras_de_produto"]]


def bloco_cobertura(fatos):
    """Todo número que uma pergunta prevista exige tem de estar no bloco de fatos.
    Se não estiver, o modelo só poderia responder inventando."""
    bloco = bloco_de_fatos(fatos)
    res = []
    for c in CASOS["cobertura"]:
        if c.get("fora_de_alcance"):
            res.append({**c, "ok": None, "faltando": []})
            continue
        faltando = [t for t in c["exige"] if t not in bloco]
        res.append({**c, "ok": not faltando, "faltando": faltando})
    return res


def relatorio(markdown: bool = False) -> int:
    fatos = levantar_fatos()
    grupos = [
        ("Correção do cálculo", bloco_calculo(fatos)),
        ("Consistência interna", bloco_consistencia(fatos)),
        ("Regras de seleção de produto", bloco_produtos(fatos)),
        ("Cobertura de fatos por pergunta", bloco_cobertura(fatos)),
    ]

    linhas, falhas, total = [], 0, 0
    marca = (lambda ok: "✅" if ok else "❌") if markdown else (lambda ok: "PASSA" if ok else "FALHA")

    for titulo, itens in grupos:
        linhas.append(f"\n## {titulo}" if markdown else f"\n=== {titulo.upper()} ===")
        if markdown:
            linhas.append("\n| Caso | O que verifica | Resultado |")
            linhas.append("|---|---|---|")
        for i in itens:
            desc = i.get("descricao") or i.get("pergunta")
            if i["ok"] is None:
                status = "— fora de alcance (avaliação manual)" if markdown else "N/A  (manual)"
            else:
                total += 1
                falhas += 0 if i["ok"] else 1
                status = marca(i["ok"])
                if not i["ok"] and "obtido" in i:
                    status += f" (esperado {i['esperado']}, obtido {i['obtido']})"
                if not i["ok"] and i.get("faltando"):
                    status += f" (ausente nos fatos: {', '.join(i['faltando'])})"
            linhas.append(f"| `{i['id']}` | {desc} | {status} |" if markdown
                          else f"  [{status:^6}] {i['id']}  {desc}")

    passou = total - falhas
    resumo = f"{passou}/{total} verificações automáticas passaram"
    manuais = sum(1 for _, it in grupos for i in it if i["ok"] is None)

    if markdown:
        cab = ["# Relatório de avaliação — Rumo", "",
               f"**{resumo}**  ·  {manuais} casos de recusa avaliados manualmente", "",
               "Gerado por `python avaliacao/avaliar.py --md`. "
               "Roda sem LLM: verifica a camada determinística, que é a origem de todos os números."]
        print("\n".join(cab + linhas))
    else:
        print("\n".join(linhas))
        print(f"\n{'-'*60}\n{resumo}  |  {manuais} casos de recusa para avaliação manual")

    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(relatorio(markdown="--md" in sys.argv))
