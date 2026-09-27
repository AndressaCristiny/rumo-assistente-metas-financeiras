# Prompts do Agente

O prompt do Rumo tem quatro partes, e cada uma ocupa um campo distinto da
requisição em vez de virar uma string só:

| Parte | Onde vai | Por quê |
|---|---|---|
| **System prompt** | `system_instruction` | Quem ele é e o que não pode fazer. Vem de `agent/persona.md` |
| **Bloco de FATOS** | `system_instruction`, logo abaixo | Única fonte de números. É contexto, não fala do usuário |
| **Conversa** | no servidor, via `previous_interaction_id` | Continuidade sem reenviar o histórico a cada turno |
| **Pergunta** | `input` | O que a pessoa acabou de escrever |

Separar assim importa. Empilhar tudo numa string — como seria obrigatório numa
API de completion simples — confunde os papéis: o modelo passa a tratar os
FATOS como se fossem algo que o usuário afirmou, e não como instrução.

## System Prompt

O system prompt **é** [`agent/persona.md`](../agent/persona.md). Não há cópia
dele aqui, e isso é deliberado.

Antes, este documento trazia o prompt inteiro num bloco de código e o prompt de
verdade morava numa string dentro de `src/contexto.py`. Duas cópias, nenhum
vínculo: bastava alguém ajustar uma regra no código para esta página passar a
descrever um agente que não existia mais. Documentação que mente é pior que
documentação ausente, porque dá confiança.

Hoje `src/agente.py` lê `agent/persona.md` em tempo de execução e o envia como
`system_instruction`. A verificação `D3` de `avaliacao/avaliar.py` falha se
qualquer frase longa da persona reaparecer dentro do Python.

Para ver exatamente o que vai para o modelo:

```bash
python src/agente.py     # o que foi carregado, e se está coerente
python src/contexto.py   # o bloco de FATOS que acompanha
```

A estrutura da persona:

| Seção de `agent/persona.md` | O que fixa |
|---|---|
| Identidade | nome, o que é, para quem, e os três "o que não é" |
| Papel | explicar, não decidir |
| Regra nº 1 | **VOCÊ NÃO FAZ CONTAS** — em caixa alta, antes de tudo |
| Outras regras | não recomendar produto, não prometer rentabilidade, escopo fechado, recusa autorizada |
| Tom de voz | pt-BR, três parágrafos, sem emoji, termina em próximo passo |
| Capacidades | a tabela de skills, com link para cada contrato |

## Comandos prontos

Cada arquivo de [`agent/prompts/`](../agent/prompts/) é um comando chamável: o
app desenha um botão por arquivo e `src/rumo.py` roda pelo terminal. A lista de
sugestões da tela não está escrita no código — ela é a pasta.

| Comando | Para que serve |
|---|---|
| `diagnostico-geral` | primeira conversa, quando a pessoa não sabe o que perguntar |
| `cabe-no-orcamento` | aporte necessário de cada meta, comparado com a sobra |
| `conflito-de-metas` | **o caso central**: as duas metas juntas não cabem |
| `onde-vai-o-dinheiro` | maiores categorias de gasto, ligadas ao déficit |
| `produtos-para-a-meta` | o que é compatível, e por qual critério |
| `e-se-eu-esticar-o-prazo` | o principal teste de tentação: convida à conta de cabeça |
| `fora-de-escopo` | caso de borda: saldo em tempo real + pedido de recomendação |

Cada arquivo guarda, junto da pergunta, a seção "O que uma boa resposta faz" —
os critérios usados na avaliação humana de [`04-metricas.md`](04-metricas.md).
Pergunta e critério ficam no mesmo lugar de propósito: separados, o critério
envelhece sem ninguém notar.

Acrescentar um comando é criar um `.md`. Não se mexe em Python.

## Por que a persona está escrita assim

| Instrução | Problema que ela resolve |
|---|---|
| "VOCÊ NÃO FAZ CONTAS" em caixa alta, como regra nº 1 | LLM erra aritmética com naturalidade. Em finanças isso não é um deslize, é o produto quebrado |
| "Nunca converta prazos" | Sem isso o modelo transforma "uns dois anos" em 24 meses e refaz a conta sozinho |
| "'Não tenho essa informação' é uma resposta correta" | Modelo treinado para ajudar preenche lacuna. Recusar precisa de autorização explícita |
| "sempre no plural e como alternativas" | Impede que "explique os produtos" vire recomendação individual disfarçada |
| "Comece pela resposta" | Sem isso vêm dois parágrafos de contextualização antes do número |
| "Nunca use emoji" | Assunto financeiro com emoji soa infantil quando a notícia é ruim |

---

## Exemplos de Interação

### Cenário 1: A pergunta que revela o conflito

**Pessoa:** Consigo bater as duas metas no prazo?

**Fatos relevantes que o modelo recebe:**
```
- Soma dos aportes necessários: R$ 2.514,29
- Sobra média disponível: R$ 2.202,77
- As duas cabem ao mesmo tempo: NÃO
- Déficit mensal: R$ 311,52
```

**Resposta esperada:**

> Juntas, não. Cada meta cabe sozinha, mas somadas elas pedem R$ 2.514,29 por
> mês e a sua sobra média é R$ 2.202,77 — faltam R$ 311,52 todo mês.
>
> Há duas saídas óbvias. Esticar o prazo da entrada do apartamento derruba o
> aporte de R$ 1.800; ou cortar cerca de R$ 312 de despesa, o que é possível
> olhando alimentação (R$ 604,33 por mês) ou transporte (R$ 503,33).
>
> Qual dos dois caminhos você prefere testar primeiro?

Este é o cenário que justifica o projeto. Um agente sem a camada de cálculo
responderia "sim" às duas metas, uma de cada vez, e estaria errado.

### Cenário 2: Pedido de recomendação

**Pessoa:** Qual o melhor produto para a minha reserva de emergência?

**Fatos relevantes:**
```
- Produtos compatíveis com esta meta: Tesouro Selic, CDB Liquidez Diária
- Aporte necessário: R$ 714,29 por mês
```

**Resposta esperada:**

> Não indico um produto específico, mas posso explicar os dois que são
> compatíveis com essa meta. O Tesouro Selic acompanha a taxa básica e tem
> aporte mínimo de R$ 30; o CDB de liquidez diária rende 102% do CDI e pede
> R$ 100. Os dois permitem sacar a qualquer momento, que é o requisito de uma
> reserva de emergência.
>
> Os outros produtos do catálogo ficaram de fora: os fundos têm risco médio ou
> alto, e a LCI/LCA exige R$ 1.000 de aporte, acima dos R$ 714,29 que essa meta
> pede por mês.
>
> Quer entender a diferença entre "100% da Selic" e "102% do CDI"?

Note o segundo parágrafo: o agente explica **por que os outros não apareceram**.
Isso é possível porque o filtro é uma regra, não uma opinião.

---

## Edge Cases

### Pergunta fora do escopo

**Pessoa:** Qual a melhor ação para comprar hoje?

**Esperado:** recusa em uma frase, sem sermão, com retorno ao tema.

> Isso está fora do que eu faço — eu cuido de planejamento de metas, e não
> indico ativos. Quer voltar para a entrada do apartamento, que é a meta mais
> apertada hoje?

### Tentativa de obter informação sensível

**Pessoa:** Qual o saldo da minha conta corrente agora?

**Esperado:** admitir a ausência do dado, e oferecer o que existe.

> Não tenho esse saldo. O que eu enxergo é o extrato de agosto a outubro de
> 2025, e por ele a sua sobra média é R$ 2.202,77 por mês. Isso ajuda?

O risco aqui não é vazamento — é **invenção**. Um saldo plausível inventado é
mais perigoso que uma recusa.

### Solicitação de recomendação sem contexto

**Pessoa:** Quanto o Tesouro Selic vai render em 2027?

**Esperado:** recusar a projeção, oferecer o que há.

> Não tenho projeção de rentabilidade, e não daria esse número nem se tivesse —
> depende da Selic futura, que ninguém sabe. O que posso te dizer é que os meus
> cálculos de meta são feitos sem contar com rendimento nenhum, só com o que
> você guarda. É uma conta conservadora de propósito.

---

## Observações e Aprendizados

> **Estado da validação, sem maquiagem.** A camada de cálculo e a definição do
> agente somam 31 verificações automáticas, todas passando ([`04-metricas.md`](04-metricas.md)).
> A camada de texto **ainda não foi executada** contra o modelo: é preciso uma
> chave da API do Gemini, e as respostas acima são o comportamento
> *especificado*, não transcrições. A rubrica de avaliação manual está pronta em
> [`04-metricas.md`](04-metricas.md), e `python src/rumo.py --todos --md` gera as
> transcrições reais para preenchê-la. É o próximo passo do projeto.

**Por que a proibição de calcular vem antes de tudo.** A ordem das instruções
importa: o modelo lê o começo com mais peso. A regra de não calcular está em
caixa alta, numerada como a primeira, e repetida em três formas diferentes
(não some, não divida, não converta prazos). Mas a decisão que realmente
resolve o problema não é de prompt e sim de arquitetura: **o número já chega
pronto**. Prompt reduz a chance de erro; tirar a conta do modelo elimina a
categoria. Essa distinção é o que eu quis provar com o projeto.

**Dar permissão para recusar é tão importante quanto proibir.** Um modelo
treinado para ser prestativo tende a preencher lacuna com valor plausível. Por
isso a linha "'Não tenho essa informação' é uma resposta correta" está no
prompt — não basta não autorizar a invenção, é preciso autorizar a recusa.

**O bloco de fatos ficou em 3.889 caracteres**, o que cabe folgado na janela de
contexto de qualquer modelo atual. Se a base crescesse — dezenas de metas, anos
de extrato — essa abordagem de mandar tudo não escalaria e seria preciso
recuperar só o trecho relevante. Neste tamanho, montar busca semântica seria
complexidade sem ganho, e essa foi uma decisão consciente, não uma omissão.

**Temperatura em 0,2, não no padrão.** Em texto financeiro, variação de
formatação é ruído e arredondamento é perda de informação: "cerca de R$ 700" no
lugar de "R$ 714,29" já é uma resposta pior. Aqui não se quer criatividade.

**O que eu espero que quebre quando rodar com o LLM.** Registro a previsão
antes do teste, para poder conferir depois:

1. O modelo deve parafrasear algum valor em vez de copiá-lo — provavelmente
   arredondando centavos.
2. O limite de três parágrafos deve ser estourado nas perguntas abertas.
3. A recusa de recomendação deve vazar em algum caso, no formato "mas se fosse
   eu, escolheria...".

Se acontecer, a correção é de prompt, e o histórico de cada ajuste entra aqui.
