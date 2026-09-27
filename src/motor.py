"""
Motor determinístico do Rumo.

Regra central do projeto: **o LLM não faz conta.**

Todo número que aparece numa resposta do agente é calculado aqui, em Python, a
partir dos arquivos de `data/`. O LLM recebe esses números já prontos e só
escreve a explicação em volta. Isso elimina a classe de alucinação mais
perigosa num contexto financeiro: o erro aritmético dito com confiança.

Este módulo não importa nada de LLM e roda sem rede — por isso ele é testável
(ver `avaliacao/avaliar.py`).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path

import pandas as pd

DADOS = Path(__file__).resolve().parent.parent / "data"


def brl(valor: float) -> str:
    """Formata em real brasileiro: 1488.48 -> 'R$ 1.488,48'."""
    return "R$ " + f"{valor:,.2f}".translate(str.maketrans(",.", ".,"))

# Data de referência do estudo de caso. Fixa para que os números do README e
# das métricas sejam reproduzíveis — trocar por date.today() em produção.
HOJE = date(2025, 11, 1)


# --------------------------------------------------------------------------- #
# Carga
# --------------------------------------------------------------------------- #

def carregar():
    perfil = json.loads((DADOS / "perfil_investidor.json").read_text(encoding="utf-8"))
    produtos = json.loads((DADOS / "produtos_financeiros.json").read_text(encoding="utf-8"))
    transacoes = pd.read_csv(DADOS / "transacoes.csv", parse_dates=["data"])
    historico = pd.read_csv(DADOS / "historico_atendimento.csv", parse_dates=["data"])
    return perfil, produtos, transacoes, historico


# --------------------------------------------------------------------------- #
# Orçamento
# --------------------------------------------------------------------------- #

@dataclass
class Orcamento:
    meses: int
    receita_media: float
    despesa_media: float
    sobra_media: float
    taxa_poupanca: float          # sobra / receita
    sobra_por_mes: dict           # {'2025-08': 1150.10, ...}
    despesa_por_categoria: dict   # média mensal por categoria
    mes_pior: str
    mes_melhor: str


def analisar_orcamento(transacoes: pd.DataFrame) -> Orcamento:
    t = transacoes.copy()
    t["mes"] = t["data"].dt.to_period("M").astype(str)

    entradas = t[t["tipo"] == "entrada"].groupby("mes")["valor"].sum()
    saidas = t[t["tipo"] == "saida"].groupby("mes")["valor"].sum()
    sobra = (entradas - saidas).dropna()

    por_cat = (
        t[t["tipo"] == "saida"].groupby("categoria")["valor"].sum() / len(sobra)
    ).round(2)

    receita_media = float(entradas.mean())
    despesa_media = float(saidas.mean())
    sobra_media = float(sobra.mean())

    return Orcamento(
        meses=len(sobra),
        receita_media=round(receita_media, 2),
        despesa_media=round(despesa_media, 2),
        sobra_media=round(sobra_media, 2),
        taxa_poupanca=round(sobra_media / receita_media, 4) if receita_media else 0.0,
        sobra_por_mes={k: round(float(v), 2) for k, v in sobra.items()},
        despesa_por_categoria=por_cat.sort_values(ascending=False).to_dict(),
        mes_pior=str(sobra.idxmin()),
        mes_melhor=str(sobra.idxmax()),
    )


# --------------------------------------------------------------------------- #
# Metas
# --------------------------------------------------------------------------- #

@dataclass
class Meta:
    id: str
    nome: str
    valor_necessario: float
    valor_atual: float
    falta: float
    progresso: float          # 0..1
    prazo: str                # 'AAAA-MM'
    meses_restantes: int
    aporte_necessario: float  # por mês, para chegar no prazo
    viavel: bool              # cabe na sobra média?
    folga: float              # sobra_media - aporte_necessario
    prazo_realista: str       # quando chegaria no ritmo atual
    diagnostico: str


def _meses_entre(inicio: date, prazo: str) -> int:
    ano, mes = (int(x) for x in prazo.split("-"))
    return max(0, (ano - inicio.year) * 12 + (mes - inicio.month))


def _soma_meses(inicio: date, n: int) -> str:
    total = (inicio.year * 12 + inicio.month - 1) + n
    return f"{total // 12:04d}-{total % 12 + 1:02d}"


def analisar_metas(perfil: dict, orcamento: Orcamento, hoje: date = HOJE) -> list[Meta]:
    """Avalia cada meta isoladamente: quanto falta, quanto precisa guardar por
    mês e se isso cabe na sobra média observada no extrato."""
    metas: list[Meta] = []

    for m in sorted(perfil["metas"], key=lambda x: x.get("prioridade", 99)):
        necessario = float(m["valor_necessario"])
        atual = float(m.get("valor_atual", 0.0))
        falta = round(max(0.0, necessario - atual), 2)
        meses = _meses_entre(hoje, m["prazo"])

        aporte = round(falta / meses, 2) if meses > 0 else falta
        folga = round(orcamento.sobra_media - aporte, 2)
        viavel = aporte <= orcamento.sobra_media

        if falta == 0:
            prazo_realista, diagnostico = "concluída", "Meta já atingida."
        elif orcamento.sobra_media <= 0:
            prazo_realista = "indefinido"
            diagnostico = "Não há sobra mensal no extrato: no ritmo atual a meta não avança."
        else:
            n = int(-(-falta // orcamento.sobra_media))  # teto da divisão
            prazo_realista = _soma_meses(hoje, n)
            if viavel:
                diagnostico = (
                    f"Viável: o aporte de {brl(aporte)} cabe na sobra média, "
                    f"com folga de {brl(folga)} por mês."
                )
            else:
                diagnostico = (
                    f"Fora do alcance no prazo: o aporte de {brl(aporte)} excede a sobra "
                    f"média em {brl(abs(folga))} por mês. No ritmo atual, a meta seria "
                    f"atingida em {prazo_realista}."
                )

        metas.append(Meta(
            id=m.get("id", m["meta"][:20]),
            nome=m["meta"],
            valor_necessario=necessario,
            valor_atual=atual,
            falta=falta,
            progresso=round(atual / necessario, 4) if necessario else 1.0,
            prazo=m["prazo"],
            meses_restantes=meses,
            aporte_necessario=aporte,
            viavel=viavel,
            folga=folga,
            prazo_realista=prazo_realista,
            diagnostico=diagnostico,
        ))

    return metas


def conflito_de_metas(metas: list[Meta], orcamento: Orcamento) -> dict:
    """As metas competem pela mesma sobra. Soma os aportes e diz se o conjunto
    cabe — um detalhe que passa despercebido quando se olha meta por meta."""
    total = round(sum(m.aporte_necessario for m in metas if m.falta > 0), 2)
    return {
        "aporte_total_necessario": total,
        "sobra_media": orcamento.sobra_media,
        "cabe_tudo": total <= orcamento.sobra_media,
        "deficit": round(max(0.0, total - orcamento.sobra_media), 2),
    }


# --------------------------------------------------------------------------- #
# Produtos
# --------------------------------------------------------------------------- #

def produtos_compativeis(produtos: list[dict], perfil: dict, meta: Meta) -> list[dict]:
    """Filtra produtos por REGRA, não por opinião do LLM.

    Critérios, todos explícitos e auditáveis:
      - meta de curto prazo (< 24 meses) ou cliente que não aceita risco → só risco baixo;
      - aporte mínimo tem de caber no aporte mensal necessário;
      - perfil conservador nunca vê produto de risco alto.
    """
    curto_prazo = meta.meses_restantes < 24
    so_baixo = curto_prazo or not perfil.get("aceita_risco", False)
    perfil_cliente = perfil.get("perfil_investidor", "moderado")

    compativeis = []
    for p in produtos:
        risco = p.get("risco", "alto")
        if so_baixo and risco != "baixo":
            continue
        if perfil_cliente == "conservador" and risco == "alto":
            continue
        if float(p.get("aporte_minimo", 0)) > max(meta.aporte_necessario, 0.01):
            continue
        compativeis.append(p)
    return compativeis


# --------------------------------------------------------------------------- #
# Fato consolidado
# --------------------------------------------------------------------------- #

def levantar_fatos(hoje: date = HOJE) -> dict:
    """Único ponto de entrada. Devolve tudo o que o agente pode afirmar."""
    perfil, produtos, transacoes, historico = carregar()
    orcamento = analisar_orcamento(transacoes)
    metas = analisar_metas(perfil, orcamento, hoje)

    return {
        "data_referencia": hoje.isoformat(),
        "cliente": {
            "nome": perfil["nome"],
            "idade": perfil["idade"],
            "perfil_investidor": perfil["perfil_investidor"],
            "aceita_risco": perfil["aceita_risco"],
            "renda_mensal": perfil["renda_mensal"],
        },
        "orcamento": asdict(orcamento),
        "metas": [asdict(m) for m in metas],
        "conflito": conflito_de_metas(metas, orcamento),
        "produtos_por_meta": {
            m.id: [p["nome"] for p in produtos_compativeis(produtos, perfil, m)]
            for m in metas
        },
        "produtos": produtos,
        "atendimentos": historico.assign(
            data=historico["data"].dt.strftime("%Y-%m-%d")
        ).to_dict("records"),
    }


if __name__ == "__main__":
    print(json.dumps(levantar_fatos(), indent=2, ensure_ascii=False))
