# Skills do Rumo

Uma skill aqui é uma **capacidade determinística**: uma função Python em
`src/motor.py` que produz números. O modelo de linguagem não executa nenhuma
delas e não decide quando chamá-las — elas rodam antes da conversa e o resultado
entra no bloco `FATOS`.

Essa é uma escolha de arquitetura, não uma limitação. Num agente financeiro o
erro que passa em silêncio é o número errado. Tirando o cálculo do modelo:

- o número é sempre o mesmo para a mesma pergunta;
- o cálculo é testável sem LLM e sem rede (`python avaliacao/avaliar.py`);
- a alucinação numérica fica sem espaço: o modelo tem a instrução de só citar
  valores que estejam nos FATOS.

Cada pasta tem um `SKILL.md` com o contrato: quando usar, entradas, saída e
limites. A ordem de execução está em `agent/skills/README.md#pipeline`.

## Pipeline

```
carregar()                      le data/*.json e data/*.csv
   |
   +-> analisar-orcamento       extrato  -> quanto sobra por mes
   |        |
   |        +-> analisar-metas               metas -> aporte necessario por meta
   |                 |
   |                 +-> detectar-conflito-de-metas   as metas cabem juntas?
   |                 |
   |                 +-> filtrar-produtos-compativeis  o que respeita perfil/prazo/aporte
   |
   v
levantar_fatos()  ->  bloco FATOS  ->  system_instruction  ->  modelo redige
```
