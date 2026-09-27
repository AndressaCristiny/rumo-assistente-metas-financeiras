---
skill: filtrar-produtos-compativeis
funcao: motor.produtos_compativeis
depende_de: analisar-metas
---

# filtrar-produtos-compativeis

## Quando usar

Quando a pergunta é "onde eu guardo esse dinheiro". Roda uma vez por meta.

## Entrada

`data/produtos_financeiros.json` (cada produto com `risco`, `liquidez` e
`aporte_minimo`), o perfil da pessoa e a `Meta`.

## O que faz

Filtra por **regra explícita**, nunca por opinião do modelo:

1. meta de curto prazo (menos de 24 meses) **ou** cliente que não aceita risco
   → só produtos de risco baixo;
2. perfil conservador nunca vê produto de risco alto;
3. o `aporte_minimo` do produto tem de caber no `aporte_necessario` da meta.

## Saída

A lista de produtos aprovados, por meta. Pode ser vazia — e nesse caso o agente
tem de dizer que não há produto compatível, não inventar um.

## Limites e por que a regra fica fora do modelo

Recomendação de produto financeiro é a parte regulada da conversa. Deixar o
modelo escolher tornaria a decisão inauditável: a mesma pergunta poderia trazer
respostas diferentes. Com a regra em Python, o critério é lido no código e
testado.

O agente tem instrução de **não recomendar um produto**: ele apresenta os
compatíveis no plural e explica o critério que os aprovou.

## Verificado por

`P1` (cliente sem apetite a risco só vê risco baixo), `P2` (curto prazo só vê
risco baixo), `P3` (aporte mínimo cabe), `P4` (nenhuma meta fica sem opção).
