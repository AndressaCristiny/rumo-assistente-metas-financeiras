"""
Carrega a definição do agente a partir da pasta `agent/`.

A identidade do Rumo, os comandos prontos e as skills ficam em arquivos de
texto, não em strings dentro do Python. Este módulo é a ponte: ele lê os
arquivos em tempo de execução.

A razão é concreta. Enquanto o system prompt vivia dentro de `contexto.py` e a
documentação era uma cópia dele em `docs/`, as duas podiam divergir sem que
ninguém percebesse — a documentação era capaz de mentir sobre o comportamento.
Agora o arquivo *é* o comportamento: `agent/persona.md` é literalmente o que vai
para o modelo, e as sugestões da tela são literalmente `agent/prompts/*.md`.

Se um arquivo obrigatório faltar, isto falha alto em vez de cair num texto
embutido de reserva — um fallback silencioso traria o problema de volta.

Ver o que foi carregado:

    python src/agente.py
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PASTA_AGENTE = RAIZ / "agent"
PERSONA = PASTA_AGENTE / "persona.md"
PASTA_PROMPTS = PASTA_AGENTE / "prompts"
PASTA_SKILLS = PASTA_AGENTE / "skills"


# --------------------------------------------------------------------------- #
# Leitura de frontmatter — sem dependência externa
# --------------------------------------------------------------------------- #

def _separar_frontmatter(texto: str) -> tuple[dict[str, str], str]:
    """Devolve (metadados, corpo). Aceita só `chave: valor` de uma linha,
    que é tudo o que este projeto precisa — não é um parser de YAML."""
    linhas = texto.lstrip().splitlines()
    if not linhas or linhas[0].strip() != "---":
        return {}, texto

    meta: dict[str, str] = {}
    for i, linha in enumerate(linhas[1:], start=1):
        if linha.strip() == "---":
            return meta, "\n".join(linhas[i + 1:]).strip()
        chave, sep, valor = linha.partition(":")
        if sep:
            meta[chave.strip()] = valor.strip()
    return meta, ""


def _secao(corpo: str, titulo: str) -> str:
    """Extrai o conteúdo de uma seção `## <titulo>` até o próximo `##`."""
    dentro, colhido = False, []
    for linha in corpo.splitlines():
        if linha.startswith("## "):
            if dentro:
                break
            dentro = linha[3:].strip().lower() == titulo.strip().lower()
            continue
        if dentro:
            colhido.append(linha)
    return "\n".join(colhido).strip()


def _sem_citacao(bloco: str) -> str:
    """Tira o `> ` do blockquote e junta as linhas num parágrafo só."""
    linhas = [l.lstrip("> ").rstrip() for l in bloco.splitlines() if l.strip()]
    return " ".join(linhas).strip()


# --------------------------------------------------------------------------- #
# Persona
# --------------------------------------------------------------------------- #

def carregar_persona() -> str:
    """O system prompt do agente, lido de agent/persona.md.

    O bloco de citação inicial é uma nota para quem lê o repositório, não
    instrução para o modelo, então é removido antes do envio.
    """
    if not PERSONA.exists():
        raise FileNotFoundError(
            f"agent/persona.md não encontrado em {PERSONA}. "
            "A identidade do agente vive nesse arquivo; sem ele não há agente."
        )
    linhas = [l for l in PERSONA.read_text(encoding="utf-8").splitlines()
              if not l.lstrip().startswith(">")]
    texto = "\n".join(linhas)
    while "\n\n\n" in texto:
        texto = texto.replace("\n\n\n", "\n\n")
    return texto.replace("\n---\n", "\n").strip()


# --------------------------------------------------------------------------- #
# Comandos prontos
# --------------------------------------------------------------------------- #

@dataclass
class Comando:
    id: str
    titulo: str
    quando: str
    skills: list[str]
    pergunta: str
    criterios: str
    arquivo: str

    @property
    def e_teste(self) -> bool:
        return self.titulo.lower().startswith("(teste)")


def listar_comandos() -> list[Comando]:
    """Todos os comandos de agent/prompts/, em ordem de arquivo."""
    comandos: list[Comando] = []
    for caminho in sorted(PASTA_PROMPTS.glob("*.md")):
        if caminho.name.lower() == "readme.md":
            continue
        meta, corpo = _separar_frontmatter(caminho.read_text(encoding="utf-8"))
        pergunta = _sem_citacao(_secao(corpo, "Pergunta"))
        if not pergunta:
            continue
        comandos.append(Comando(
            id=meta.get("comando", caminho.stem),
            titulo=meta.get("titulo", caminho.stem),
            quando=meta.get("quando", ""),
            skills=[s.strip() for s in meta.get("skills", "").split(",") if s.strip()],
            pergunta=pergunta,
            criterios=_secao(corpo, "O que uma boa resposta faz"),
            arquivo=str(caminho.relative_to(RAIZ)).replace("\\", "/"),
        ))
    return comandos


def comando(ident: str) -> Comando:
    for c in listar_comandos():
        if c.id == ident:
            return c
    disponiveis = ", ".join(c.id for c in listar_comandos())
    raise KeyError(f"Comando '{ident}' não existe. Disponíveis: {disponiveis}")


# --------------------------------------------------------------------------- #
# Skills
# --------------------------------------------------------------------------- #

@dataclass
class Skill:
    id: str
    funcao: str
    depende_de: str
    quando: str
    limites: str
    arquivo: str
    titulo: str = ""
    corpo: str = field(default="", repr=False)


def listar_skills() -> list[Skill]:
    """Todas as skills declaradas em agent/skills/*/SKILL.md."""
    skills: list[Skill] = []
    for caminho in sorted(PASTA_SKILLS.glob("*/SKILL.md")):
        meta, corpo = _separar_frontmatter(caminho.read_text(encoding="utf-8"))
        titulo = next((l[2:].strip() for l in corpo.splitlines() if l.startswith("# ")), "")
        skills.append(Skill(
            id=meta.get("skill", caminho.parent.name),
            funcao=meta.get("funcao", ""),
            depende_de=meta.get("depende_de", ""),
            quando=_secao(corpo, "Quando usar"),
            limites=_secao(corpo, "Limites") or _secao(corpo, "Limites e por que a regra fica fora do modelo"),
            arquivo=str(caminho.relative_to(RAIZ)).replace("\\", "/"),
            titulo=titulo,
            corpo=corpo,
        ))
    return skills


# --------------------------------------------------------------------------- #
# Conferência rápida
# --------------------------------------------------------------------------- #

def _resumo() -> int:
    persona = carregar_persona()
    comandos = listar_comandos()
    skills = listar_skills()

    print(f"persona.md .......... {len(persona)} caracteres")
    print(f"comandos ............ {len(comandos)}")
    for c in comandos:
        marca = "teste" if c.e_teste else "    "
        print(f"  [{marca}] {c.id:24} {c.pergunta[:58]}")
    print(f"skills .............. {len(skills)}")
    for s in skills:
        print(f"         {s.id:32} -> {s.funcao}")

    problemas = []
    declaradas = {s.id for s in skills}
    for c in comandos:
        for nome in c.skills:
            if nome not in declaradas:
                problemas.append(f"{c.arquivo}: skill '{nome}' não tem SKILL.md")
    if "VOCÊ NÃO FAZ CONTAS" not in persona:
        problemas.append("persona.md perdeu a regra nº 1 (VOCÊ NÃO FAZ CONTAS)")

    print()
    if problemas:
        for p in problemas:
            print(f"PROBLEMA: {p}")
        return 1
    print("Definição do agente consistente: toda skill citada tem SKILL.md.")
    return 0


if __name__ == "__main__":
    raise SystemExit(_resumo())
