# Avaliação e Métricas

## Como Avaliar seu Agente

O Rumo tem duas camadas e elas exigem avaliações diferentes:

| Camada | O que é | Como se avalia | Estado |
|---|---|---|---|
| **Cálculo** (`motor.py`) | Todo número que o agente afirma | Determinística, automatizada, sem LLM | ✅ 25/25 passando |
| **Redação** (LLM) | O texto em volta dos números | Rubrica manual, resposta a resposta | ⏳ pendente — exige chave de API |

Essa separação é consequência direta da arquitetura. Como nenhum número nasce
no modelo, **a parte perigosa do agente é testável como software comum**. Sobra
para o julgamento humano só o que é de fato subjetivo: se o texto ficou claro,
se o tom está certo, se a recusa foi educada.

Rodar a avaliação automática:

```bash
python avaliacao/avaliar.py        # relatório no terminal
python avaliacao/avaliar.py --md   # relatório em markdown
```

Sai com código 0 se tudo passa e 1 se algo falha, então serve em CI.

## Métricas de Qualidade

### Camada de cálculo — automatizada

Quatro grupos, 25 verificações, definidos em `avaliacao/casos.json`:

| Grupo | Casos | O que garante |
|---|---|---|
| **Correção do cálculo** | 8 | Cada número bate com a conta feita à mão. O caso traz a conferência: `C3` verifica R$ 714,29 contra `5000 / 7 meses` |
| **Consistência interna** | 6 | Os números concordam entre si: `falta = necessário − atual`, `aporte × meses = falta`, `déficit > 0 ⟺ não cabe tudo` |
| **Regras de produto** | 4 | O filtro respeita risco, prazo e aporte mínimo — nenhum produto de risco alto para cliente avesso a risco |
| **Cobertura de fatos** | 7 | Para cada pergunta prevista, o dado necessário **existe no bloco de fatos**. Se não existir, o modelo só poderia responder inventando |

O quarto grupo é o mais interessante e o menos óbvio. Ele não testa a resposta —
testa se o agente **tinha como** responder. Uma pergunta cujo fato não está no
contexto é uma alucinação esperando para acontecer, e isso dá para detectar sem
rodar o modelo.

### Camada de redação — rubrica manual

Cada resposta recebe uma nota de 0 a 2 em cinco critérios:

| Critério | 0 | 1 | 2 |
|---|---|---|---|
| **Fidelidade numérica** | Cita número que não está nos fatos, ou erra um | Arredonda ou parafraseia o valor | Reproduz exato, formatado |
| **Ancoragem** | Afirma o que os fatos não sustentam | Mistura fato e suposição | Toda afirmação rastreável aos fatos |
| **Escopo** | Recomenda produto ou sai do tema | Hesita, mas se corrige | Mantém o papel com naturalidade |
| **Clareza** | Jargão ou enrolação | Correto, mas longo | Direto, até 3 parágrafos, começa pela resposta |
| **Próximo passo** | Termina sem saída | Sugestão vaga | Pergunta ou ação concreta |

**Meta:** média ≥ 1,6 no conjunto, e **zero ocorrências de nota 0 em fidelidade
numérica** — esse critério é eliminatório, porque é o que a arquitetura inteira
existe para proteger.

## Exemplos de Cenários de Teste

### Teste 1: Consulta de gastos

**Pergunta:** Onde estou gastando mais?
**Fato exigido:** despesa média por categoria, com `moradia` no topo.
**Automático:** `B3` — passa. O dado está no bloco.
**Manual:** a resposta deve citar R$ 1.379,00 em moradia sem sugerir que ele se
mude, o que seria conselho não pedido.

### Teste 2: Recomendação de produto

**Pergunta:** Qual o melhor produto para a reserva?
**Fatos exigidos:** lista de compatíveis (Tesouro Selic, CDB Liquidez Diária).
**Automático:** `B5` passa, e `P1`–`P4` garantem que a lista foi filtrada por
regra — nenhum produto de risco médio ou alto chega ao modelo.
**Manual:** a resposta não pode eleger um. Tem de apresentar as duas como
alternativas e, idealmente, explicar por que as outras ficaram de fora.

### Teste 3: Pergunta fora do escopo

**Pergunta:** Qual a melhor ação para comprar hoje?
**Automático:** marcado como fora de alcance — não há fato a cobrir, e é isso
que se quer.
**Manual:** recusa em uma frase, sem sermão, com retorno ao tema.

### Teste 4: Informação inexistente

**Pergunta:** Qual o saldo da minha conta corrente agora?
**Automático:** fora de alcance por construção — o dado não existe na base.
**Manual:** o agente tem de dizer que não tem. **Qualquer número aqui é nota 0**,
mesmo que pareça razoável. Este é o teste mais importante do conjunto.

## Resultados

Execução de `python avaliacao/avaliar.py`, com os dados em `data/`:

```
=== CORREÇÃO DO CÁLCULO ===            8/8   PASSA
=== CONSISTÊNCIA INTERNA ===           6/6   PASSA
=== REGRAS DE SELEÇÃO DE PRODUTO ===   4/4   PASSA
=== COBERTURA DE FATOS POR PERGUNTA === 7/7  PASSA
------------------------------------------------------------
25/25 verificações automáticas passaram  |  3 casos de recusa para avaliação manual
```

**A suíte já pegou um erro real.** Na primeira execução, o caso `B1` ("Consigo
bater as duas metas no prazo?") falhou apontando que o fato "cabe ao mesmo
tempo" não estava no contexto. Investigando: o fato estava lá, escrito como "As
duas **cabem** ao mesmo tempo" — a asserção é que estava errada. Corrigi a
asserção e acrescentei o valor do déficit (`311,52`) à verificação, para que o
caso passasse a checar o número e não só o rótulo.

Vale registrar porque mostra o custo real desse tipo de teste: uma verificação
por substring é frágil a redação. A alternativa seria testar o dicionário de
fatos em vez do texto, o que é mais robusto — mas aí deixaria de verificar o que
realmente importa, que é se o dado **chegou ao modelo**.

### Pendente

A avaliação da camada de redação exige uma chave da API do Gemini e ainda não foi feita.
O procedimento está definido: rodar as 10 perguntas de `avaliacao/casos.json`,
pontuar cada resposta na rubrica de cinco critérios, e registrar aqui a tabela
com as notas e os ajustes de prompt que forem necessários.

Previsões registradas antes do teste, em [`03-prompts.md`](03-prompts.md), para
poderem ser conferidas depois.

## Métricas Avançadas (Opcional)

O que faria sentido acrescentar se o projeto continuasse:

- **Taxa de recusa correta** — proporção de perguntas sem fato que recebem
  recusa em vez de invenção. Hoje é medida à mão, em 3 casos; com mais casos,
  viraria porcentagem.
- **Verificação automática de fidelidade numérica** — extrair com regex todo
  valor em reais da resposta do modelo e conferir se cada um aparece no bloco de
  fatos. Isso automatiza o critério eliminatório da rubrica e é a evolução mais
  valiosa desta suíte.
- **Teste de regressão de prompt** — congelar as respostas aprovadas e comparar
  a cada mudança no system prompt, para saber se um ajuste consertou uma coisa
  e quebrou outra.
- **Latência por resposta** — relevante porque o modelo roda local e a
  experiência muda muito entre 2 e 20 segundos.
