# Base de Conhecimento

## Dados Utilizados

Quatro arquivos em `data/`, todos mockados e sem dado pessoal real.

| Arquivo | Formato | O que traz | Para que o Rumo usa |
|---|---|---|---|
| `perfil_investidor.json` | JSON | Dados do cliente, perfil de risco e **as metas com valor e prazo** | É a espinha dorsal: sem meta com prazo, não há o que planejar |
| `transacoes.csv` | CSV | 33 lançamentos, 3 meses (ago–out/2025) | Calcular quanto sobra de verdade por mês, e em quê o dinheiro vai |
| `produtos_financeiros.json` | JSON | 5 produtos com risco, rentabilidade e aporte mínimo | Filtrar o que é compatível com cada meta |
| `historico_atendimento.csv` | CSV | 5 atendimentos anteriores | Dar continuidade — o agente sabe o que já foi conversado |

## Adaptações nos Dados

O repositório base autoriza adaptar os dados. Fiz três mudanças, cada uma para
destravar algo que o agente precisava:

**1. Extrato de 1 para 3 meses (10 → 33 lançamentos).**
Com um único mês, "sobra média" é só "a sobra daquele mês". Com três, dá para
ver variação — e ela é grande: R$ 1.907,10 no pior mês contra R$ 2.511,10 no
melhor. A diferença é uma manutenção de carro de R$ 640 em setembro. Um
planejamento que ignora esse tipo de evento é otimista demais.

**2. Campo `valor_atual` em cada meta.**
O arquivo original só tinha `valor_necessario`. Sem saber quanto já foi
guardado, não há como calcular progresso nem quanto falta. Atribuí R$ 10.000 à
reserva (coerente com `reserva_emergencia_atual`) e R$ 5.000 à entrada do
apartamento.

**3. Campos `id` e `prioridade` nas metas.**
O `id` permite referenciar a meta no código e nos testes sem depender do texto.
A `prioridade` define a ordem de exibição — reserva antes de apartamento, que é
a ordem correta de qualquer planejamento.

Uma categoria nova (`educacao`) apareceu no extrato ampliado. Nada mais foi
alterado: o catálogo de produtos e o histórico de atendimento são os originais.

## Estratégia de Integração

### Como os dados são carregados?

`src/motor.py` lê os quatro arquivos com `json` e `pandas`, na função
`carregar()`. Não há banco, índice vetorial nem RAG — com uma base deste
tamanho, tudo cabe no contexto do modelo, e acrescentar busca semântica seria
complexidade sem ganho.

O caminho é resolvido a partir da posição do próprio arquivo
(`Path(__file__).parent.parent / "data"`), então o projeto roda de qualquer
diretório.

### Como os dados são usados no prompt?

Os dados **não** vão crus para o modelo. Esse é o ponto central do projeto.

```
data/ ──> motor.py ──> fatos calculados ──> contexto.py ──> bloco FATOS ──> LLM
          (Python)      (dict)                (texto)
```

O `motor.py` transforma dado bruto em **afirmação pronta**. O modelo nunca vê
`5000 / 7`; ele vê "Aporte necessário: R$ 714,29 por mês". A diferença importa
porque LLM não erra ao copiar um número — erra ao calculá-lo.

O que o motor entrega:

- **Orçamento**: receita, despesa e sobra médias, sobra mês a mês, despesa por
  categoria, melhor e pior mês.
- **Por meta**: falta, progresso, meses restantes, aporte necessário, se cabe na
  sobra, folga, prazo realista no ritmo atual e um diagnóstico em texto.
- **Conflito**: soma dos aportes contra a sobra, e o déficit. Esta é a
  informação que nenhuma das outras revela.
- **Produtos compatíveis por meta**, filtrados por regra.

O filtro de produto merece destaque porque é onde a maioria dos agentes deixa o
LLM opinar. Aqui são três regras em Python, todas auditáveis:

| Regra | Efeito nesta base |
|---|---|
| Meta com prazo < 24 meses aceita só risco baixo | A reserva (7 meses) exclui os dois fundos |
| Cliente com `aceita_risco: false` aceita só risco baixo | Vale para as duas metas deste cliente |
| Aporte mínimo do produto tem de caber no aporte da meta | LCI/LCA (mínimo R$ 1.000) sai da reserva, cujo aporte é R$ 714,29 |

Resultado: reserva → Tesouro Selic e CDB Liquidez Diária. Apartamento → esses
dois mais LCI/LCA. O modelo recebe essa lista pronta e é instruído a não
acrescentar nada.

## Exemplo de Contexto Montado

Trecho real gerado por `python src/contexto.py` (3.889 caracteres no total):

```text
DATA DE REFERÊNCIA: 2025-11-01

CLIENTE
- Nome: João Silva, 32 anos
- Perfil de investidor: moderado | aceita risco: não
- Renda mensal: R$ 5.000,00

ORÇAMENTO (média de 3 meses de extrato)
- Receita média: R$ 5.000,00
- Despesa média: R$ 2.797,23
- Sobra média: R$ 2.202,77 (44.1% da receita)
- Sobra por mês: 2025-08 = R$ 2.190,10, 2025-09 = R$ 1.907,10, 2025-10 = R$ 2.511,10
- Melhor mês: 2025-10 | pior mês: 2025-09
- Despesa média por categoria: moradia = R$ 1.379,00, alimentacao = R$ 604,33, ...

METAS
* Completar reserva de emergência (id: reserva)
  - Objetivo: R$ 15.000,00 | já guardado: R$ 10.000,00 | falta: R$ 5.000,00 | progresso: 66.7%
  - Prazo desejado: 2026-06 (7 meses a partir da data de referência)
  - Aporte necessário: R$ 714,29 por mês
  - Cabe na sobra média sozinha: sim | folga: R$ 1.488,48
  - Prazo no ritmo atual (usando toda a sobra): 2026-02
  - Diagnóstico: Viável: o aporte de R$ 714,29 cabe na sobra média, com folga de R$ 1.488,48 por mês.
  - Produtos compatíveis com esta meta: Tesouro Selic, CDB Liquidez Diária

* Entrada do apartamento (id: apartamento)
  - Objetivo: R$ 50.000,00 | já guardado: R$ 5.000,00 | falta: R$ 45.000,00 | progresso: 10.0%
  - Prazo desejado: 2027-12 (25 meses a partir da data de referência)
  - Aporte necessário: R$ 1.800,00 por mês
  ...

AS DUAS METAS JUNTAS (competem pela mesma sobra)
- Soma dos aportes necessários: R$ 2.514,29
- Sobra média disponível: R$ 2.202,77
- As duas cabem ao mesmo tempo: NÃO
- Déficit mensal: R$ 311,52
```

Repare no último bloco. Ele não está em nenhum arquivo de `data/` — é uma
conclusão, calculada. É o pedaço mais valioso do contexto, e o modelo só precisa
saber ler.

> **Nota sobre a data de referência.** O motor usa `HOJE = date(2025, 11, 1)`
> fixo, e não `date.today()`. Sem isso, o número de meses até a meta mudaria a
> cada execução e os testes automáticos quebrariam sozinhos com o passar do
> tempo. Em produção seria a data real; num projeto de portfólio, reprodutível
> vale mais.
