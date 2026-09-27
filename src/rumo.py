"""
Rumo pela linha de comando — roda os comandos de `agent/prompts/` sem Streamlit.

    python src/rumo.py                        lista os comandos disponiveis
    python src/rumo.py conflito-de-metas      roda um comando
    python src/rumo.py --todos                roda todos, em sequencia
    python src/rumo.py --todos --md > saida.md    relatorio em markdown

Serve para duas coisas: conferir a conexao com a API e gerar o material da
avaliacao humana de `docs/04-metricas.md` sem copiar e colar da tela.

Precisa da GOOGLE_API_KEY no .env. A camada de calculo nao precisa de chave —
para ver so os numeros, rode `python src/contexto.py`.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import agente                                        # noqa: E402
import llm                                           # noqa: E402
from contexto import SYSTEM_PROMPT, bloco_de_fatos   # noqa: E402


def _listar() -> int:
    print("Comandos disponiveis (agent/prompts/):\n")
    for c in agente.listar_comandos():
        marca = " [caso de borda]" if c.e_teste else ""
        print(f"  {c.id}{marca}")
        print(f"      {c.quando}")
        if c.skills:
            print(f"      skills: {', '.join(c.skills)}")
        print()
    print("Rode:  python src/rumo.py <comando>")
    return 0


def _executar(comandos: list[agente.Comando], markdown: bool) -> int:
    diag = llm.verificar()
    if not diag.pronto:
        print(diag.recado, file=sys.stderr)
        return 1

    fatos = bloco_de_fatos()
    falhas = 0

    if markdown:
        print("# Respostas do Rumo — execucao dos comandos\n")
        print(f"Modelo: `{llm.MODELO_PADRAO}` · temperatura {llm.TEMPERATURA}")
        print("\nGerado por `python src/rumo.py --todos --md`. "
              "Cada secao traz a pergunta exata do arquivo de comando e a resposta recebida.\n")

    for c in comandos:
        if markdown:
            print(f"\n## {c.titulo}\n")
            print(f"Comando `{c.id}` · arquivo `{c.arquivo}`\n")
            print(f"**Pergunta:** {c.pergunta}\n")
        else:
            print("=" * 70)
            print(f"{c.id}  ({c.arquivo})")
            print("-" * 70)
            print(f"Pergunta: {c.pergunta}\n")

        try:
            texto, _ = llm.responder(SYSTEM_PROMPT, fatos, c.pergunta)
        except Exception as erro:  # noqa: BLE001
            falhas += 1
            recado = f"FALHOU: {type(erro).__name__}: {erro}"
            print(f"> {recado}" if markdown else recado)
            continue

        print(texto)
        if markdown and c.criterios:
            print(f"\n<details><summary>Critérios de avaliação</summary>\n\n{c.criterios}\n\n</details>")
        print()

    if not markdown:
        print("=" * 70)
        print(f"{len(comandos) - falhas}/{len(comandos)} comandos responderam.")
    return 1 if falhas else 0


def main(argv: list[str]) -> int:
    markdown = "--md" in argv
    resto = [a for a in argv if not a.startswith("--")]

    if "--todos" in argv:
        return _executar(agente.listar_comandos(), markdown)
    if not resto:
        return _listar()
    try:
        escolhido = agente.comando(resto[0])
    except KeyError as erro:
        print(erro, file=sys.stderr)
        return 2
    return _executar([escolhido], markdown)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
