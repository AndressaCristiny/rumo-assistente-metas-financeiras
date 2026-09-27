"""
Camada de LLM do Rumo — API do Gemini (Google AI Studio).

Só existe uma coisa acontecendo aqui: mandar o system prompt e os FATOS já
calculados para o modelo, e receber texto de volta. Nenhum número é produzido
nesta camada — ver `motor.py`.

Por que Gemini: a camada gratuita do AI Studio cobre os modelos Flash, não
exige cartão e não exige baixar modelo nenhum. O agente é uma tarefa de
redação sobre números prontos, não de raciocínio pesado, então o modelo mais
leve dá conta.

Configuração: crie um arquivo `.env` na raiz do projeto com

    GOOGLE_API_KEY=...

Gere a chave em https://aistudio.google.com/apikey
A chave nunca entra no código nem no repositório (`.env` está no .gitignore).

Teste rápido da conexão, sem abrir o Streamlit:

    python src/llm.py --teste
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# Modelos da camada gratuita. Flash-Lite é o padrão: mais rápido e suficiente
# para redigir sobre fatos prontos.
MODELOS = {
    "Gemini 3.5 Flash-Lite — mais rápido": "gemini-3.5-flash-lite",
    "Gemini 3.8 Flash — mais capaz": "gemini-3.8-flash",
}
MODELO_PADRAO = "gemini-3.5-flash-lite"

# Temperatura baixa de propósito: aqui não se quer criatividade, se quer
# fidelidade aos números. Ver docs/03-prompts.md.
TEMPERATURA = 0.2
MAX_TOKENS = 700


def carregar_env() -> None:
    """Lê o .env da raiz sem depender de biblioteca externa."""
    caminho = RAIZ / ".env"
    if not caminho.exists():
        return
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#") or "=" not in linha:
            continue
        chave, _, valor = linha.partition("=")
        os.environ.setdefault(chave.strip(), valor.strip().strip('"').strip("'"))


def obter_chave() -> str | None:
    carregar_env()
    for nome in ("GOOGLE_API_KEY", "GEMINI_API_KEY"):
        valor = os.environ.get(nome, "").strip()
        if valor:
            return valor
    return None


@dataclass
class Diagnostico:
    pronto: bool
    recado: str


def verificar() -> Diagnostico:
    if obter_chave() is None:
        return Diagnostico(
            False,
            "Nenhuma chave encontrada. Crie um arquivo .env na raiz com "
            "GOOGLE_API_KEY=sua-chave (gere de graça em aistudio.google.com/apikey).",
        )
    try:
        import google.genai  # noqa: F401
    except ImportError:
        return Diagnostico(
            False,
            "Biblioteca google-genai não instalada. Rode: pip install -r requirements.txt",
        )
    return Diagnostico(True, "Chave carregada do .env e biblioteca pronta.")


def responder(
    system_prompt: str,
    fatos: str,
    pergunta: str,
    interacao_anterior: str | None = None,
    modelo: str = MODELO_PADRAO,
) -> tuple[str, str | None]:
    """Devolve (texto da resposta, id desta interação).

    O bloco de FATOS vai no `system_instruction`, junto das instruções, e não
    na mensagem do usuário — fatos são contexto, não fala de quem pergunta.

    O histórico da conversa fica no servidor: em vez de reenviar tudo a cada
    pergunta, passamos o id da interação anterior. Devolvemos o id novo para
    que o app encadeie o próximo turno.
    """
    from google import genai

    cliente = genai.Client(api_key=obter_chave())

    instrucao = (
        system_prompt
        + "\n\n"
        + "=" * 60
        + "\nFATOS (única fonte de números permitida)\n"
        + "=" * 60
        + "\n"
        + fatos
    )

    parametros = {
        "model": modelo,
        "input": pergunta,
        "system_instruction": instrucao,
        "generation_config": {
            "temperature": TEMPERATURA,
            "max_output_tokens": MAX_TOKENS,
        },
    }
    if interacao_anterior:
        parametros["previous_interaction_id"] = interacao_anterior

    interacao = cliente.interactions.create(**parametros)
    return (interacao.output_text or "").strip(), getattr(interacao, "id", None)


def _teste() -> int:
    """Confere a conexão de ponta a ponta com uma pergunta real do caderno."""
    diag = verificar()
    print(diag.recado)
    if not diag.pronto:
        return 1

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from contexto import SYSTEM_PROMPT, bloco_de_fatos

    pergunta = "Consigo bater as duas metas no prazo?"
    print(f"\nPergunta: {pergunta}\n" + "-" * 60)
    try:
        texto, ident = responder(SYSTEM_PROMPT, bloco_de_fatos(), pergunta)
    except Exception as erro:  # noqa: BLE001
        print(f"FALHOU: {type(erro).__name__}: {erro}")
        return 1
    print(texto)
    print("-" * 60)
    print(f"id da interação: {ident}")

    # Conferência rápida do que mais importa: o número saiu certo?
    esperado = "311,52"
    print(f"\nContém o déficit de R$ {esperado}? {'sim' if esperado in texto else 'NÃO — conferir'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_teste() if "--teste" in sys.argv else _teste())
