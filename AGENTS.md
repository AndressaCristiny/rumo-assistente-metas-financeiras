# Rumo — definição do agente

Este arquivo é o índice de **o que o agente é**. Ele não descreve o código: os
arquivos listados aqui são lidos em tempo de execução e são o comportamento.

```
agent/
├── persona.md                        identidade, papel, regras, tom de voz
├── prompts/                          comandos prontos (1 arquivo = 1 botão)
│   ├── 01-diagnostico-geral.md
│   ├── 02-cabe-no-orcamento.md
│   ├── 03-conflito-de-metas.md            <- o caso central
│   ├── 04-onde-vai-o-dinheiro.md
│   ├── 05-produtos-para-a-meta.md
│   ├── 06-e-se-eu-esticar-o-prazo.md
│   └── 07-fora-de-escopo.md               <- caso de borda
└── skills/                           capacidades determinísticas
    ├── analisar-orcamento/SKILL.md
    ├── analisar-metas/SKILL.md
    ├── detectar-conflito-de-metas/SKILL.md
    └── filtrar-produtos-compativeis/SKILL.md
```

## Quem lê o quê

| Arquivo | Lido por | Vira o quê |
|---|---|---|
| `agent/persona.md` | `src/agente.py` → `src/contexto.py` | `system_instruction` enviado ao modelo |
| `agent/prompts/*.md` | `src/agente.py` | botões na tela e comandos de `src/rumo.py` |
| `agent/skills/*/SKILL.md` | `src/agente.py` | painel de skills na barra lateral |
| `data/*` | `src/motor.py` | bloco `FATOS` |

Não existe cópia do system prompt dentro do Python. Se `agent/persona.md`
desaparecer, o app não sobe — de propósito. Um texto de reserva escondido no
código traria de volta o problema que essa separação resolve: documentação e
comportamento divergindo em silêncio.

## Como o agente funciona em uma frase

O Python calcula todos os números antes da conversa; o modelo só redige sobre
eles, com a instrução de que **não pode fazer conta nenhuma**.

```
data/ ──> motor.py (skills) ──> bloco FATOS ──┐
                                              ├──> modelo ──> resposta
agent/persona.md ──> system_instruction ──────┘
```

O que isso compra: o número é sempre o mesmo para a mesma pergunta, o cálculo é
testável sem LLM e sem rede, e a alucinação numérica fica sem espaço.

## Comandos

```bash
python src/agente.py          # o que foi carregado de agent/, e se está coerente
python src/contexto.py        # o bloco FATOS (não precisa de chave de API)
python src/rumo.py            # lista os comandos prontos
python src/rumo.py conflito-de-metas   # roda um comando contra o modelo
python avaliacao/avaliar.py   # a suíte de verificação determinística
streamlit run src/app.py      # a interface
```

## Como mexer no agente sem tocar em Python

| Quero… | Edito |
|---|---|
| mudar o tom ou uma regra | `agent/persona.md` |
| acrescentar um comando | um novo `.md` em `agent/prompts/` |
| documentar uma capacidade nova | uma pasta nova em `agent/skills/` |
| mudar os dados do cliente | `data/` |

Depois de editar, `python src/agente.py` confere se tudo continua coerente —
toda skill citada num comando precisa ter um `SKILL.md`, e a persona precisa
manter a regra nº 1.

## Onde está o resto

- `docs/01-documentacao-agente.md` — caso de uso, arquitetura, anti-alucinação
- `docs/02-base-conhecimento.md` — de onde vêm os dados
- `docs/03-prompts.md` — decisões de engenharia de prompt
- `docs/04-metricas.md` — avaliação
- `docs/05-pitch.md` — roteiro de 3 minutos
