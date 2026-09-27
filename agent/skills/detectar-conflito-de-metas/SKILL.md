---
skill: detectar-conflito-de-metas
funcao: motor.conflito_de_metas
depende_de: analisar-metas
---

# detectar-conflito-de-metas

## Quando usar

Quando há mais de uma meta ativa. É a skill que sustenta o projeto.

## O que faz

Soma os aportes necessários de todas as metas que ainda têm saldo a cobrir e
compara a soma com a **mesma** sobra média. As metas competem pelo mesmo
dinheiro; olhar meta por meta esconde isso.

## Saída

| Campo | Significado |
|---|---|
| `aporte_total_necessario` | soma dos aportes de todas as metas em aberto |
| `sobra_media` | o que existe para distribuir |
| `cabe_tudo` | `True` se a soma cabe na sobra |
| `deficit` | quanto falta por mês, se não cabe |

## Por que isso importa

Nos dados deste projeto, **cada meta cabe sozinha e as duas juntas não cabem**:
falta `R$ 311,52` por mês. Esse número não está em nenhum arquivo de dados — ele
só existe porque foi calculado. Um agente que apenas recuperasse trechos da base
não teria como responder "não, não dá".

## Limites

- Supõe que todas as metas avançam ao mesmo tempo. Não propõe o melhor
  sequenciamento — quem decide a prioridade é a pessoa.
- Não modela aporte parcial: é tudo ou o déficit.

## Verificado por

`K3` (soma dos aportes) e `K4` (`deficit > 0` ↔ `not cabe_tudo`).
