---
skill: analisar-orcamento
funcao: motor.analisar_orcamento
depende_de: carregar
---

# analisar-orcamento

## Quando usar

Sempre. É a base de tudo: nenhuma pergunta sobre meta pode ser respondida sem
saber quanto sobra por mês.

## Entrada

`data/transacoes.csv` — extrato de 3 meses, com `data`, `tipo` (entrada/saida),
`categoria` e `valor`.

## O que faz

Agrupa o extrato por mês, separa entradas de saídas e tira a média. A sobra é
calculada mês a mês e só depois a média — não é `receita_media - despesa_media`
de meses diferentes misturados.

## Saída

| Campo | Significado |
|---|---|
| `receita_media` | entrada média mensal |
| `despesa_media` | saída média mensal |
| `sobra_media` | quanto sobra, em média, por mês |
| `taxa_poupanca` | `sobra_media / receita_media` |
| `sobra_por_mes` | a sobra de cada mês, sem média |
| `despesa_por_categoria` | média mensal por categoria, em ordem decrescente |
| `mes_pior` / `mes_melhor` | os extremos, para mostrar a variação |

## Limites

- 3 meses é uma amostra curta. `sobra_por_mes` vai junto nos FATOS justamente
  para que a média não seja lida como garantia.
- Não projeta o futuro. Não considera inflação nem rendimento.

## Verificado por

`K5` (sobra = receita − despesa) e os casos de cálculo em `avaliacao/casos.json`.
