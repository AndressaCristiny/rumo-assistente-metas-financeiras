---
skill: analisar-metas
funcao: motor.analisar_metas
depende_de: analisar-orcamento
---

# analisar-metas

## Quando usar

Quando a pergunta é sobre **uma** meta: quanto falta, quanto guardar por mês,
dá ou não dá no prazo.

## Entrada

`data/perfil_investidor.json` (metas, com `valor_necessario`, `valor_atual`,
`prazo` e `prioridade`) e a saída de `analisar-orcamento`.

## O que faz

Para cada meta, em ordem de prioridade:

1. `falta = valor_necessario - valor_atual`
2. `meses_restantes` = meses entre a data de referência e o prazo
3. `aporte_necessario = falta / meses_restantes`
4. `viavel = aporte_necessario <= sobra_media`
5. `prazo_realista` = quando chegaria usando **toda** a sobra (teto da divisão)

## Saída

Uma lista de `Meta`, com `falta`, `progresso`, `aporte_necessario`, `viavel`,
`folga`, `prazo_realista` e um `diagnostico` em texto.

## Limites

- Trata cada meta **isolada**, como se ela fosse a única. É por isso que existe
  a skill `detectar-conflito-de-metas`: aqui as duas metas parecem viáveis.
- `prazo_realista` supõe a sobra inteira dedicada a essa meta — o que só vale
  se a outra meta parar.
- A data de referência é fixa (`HOJE = 2025-11-01`) para o projeto ser
  reproduzível: quem clonar o repositório em outro mês vê os mesmos números.

## Verificado por

`K1` (falta), `K2` (aporte × meses = falta), `K6` (viável ↔ aporte ≤ sobra).
