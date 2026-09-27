# Pitch (3 minutos)

## Roteiro Sugerido

### 1. O Problema (30 seg)

> "Quem tem duas metas financeiras costuma avaliar uma de cada vez. Eu pego o
> caso do João: quer fechar a reserva de emergência até junho e juntar a entrada
> de um apartamento até o fim de 2027.
>
> Pergunte a qualquer assistente se a reserva cabe no orçamento dele. Cabe.
> Pergunte se a entrada cabe. Também cabe. Só que as duas dividem a mesma sobra
> no fim do mês — e juntas não cabem. Faltam R$ 311,52 todo mês, e nada no
> extrato dele avisa isso.
>
> Esse é o primeiro problema. O segundo é pior: um assistente financeiro que
> erra uma conta é pior do que nenhum assistente. E modelo de linguagem erra
> conta com uma naturalidade constrangedora."

### 2. A Solução (1 min)

> "O Rumo é um assistente de planejamento de metas com uma decisão de
> arquitetura no centro: **o modelo de linguagem não faz contas.**
>
> Toda aritmética acontece em Python. O motor lê o extrato, calcula quanto sobra
> por mês de verdade, calcula quanto falta em cada meta, o aporte necessário, e
> — o que ninguém faz — soma os aportes para ver se o conjunto cabe.
>
> Só depois disso o modelo entra, e ele recebe os números já prontos com uma
> instrução explícita: não some, não divida, não estime. Se o número não estiver
> nos fatos, diga que não sabe.
>
> A consequência prática é que a alucinação mais perigosa em finanças, o erro
> aritmético dito com segurança, deixa de ser possível. Não porque eu pedi bem
> no prompt — porque a conta não passa pelo modelo."

### 3. Demonstração (1 min)

Sequência sugerida, com a tela dividida entre o painel lateral e a conversa:

1. **Mostre o painel primeiro.** "Tudo isto aqui é Python, não é o modelo.
   Sobra média de R$ 2.202,77, duas metas, e este aviso: as duas somam
   R$ 2.514,29 por mês."
2. **Clique no botão "As duas metas cabem juntas?"** — e diga que o botão não
   está escrito no código: "cada botão é um arquivo em `agent/prompts/`.
   Acrescentar um comando aqui é criar um markdown."
3. **Clique em "(teste) Pergunta fora do escopo"** — para mostrar a recusa.
   "Esse dado não existe na base, e o agente diz isso em vez de inventar um
   valor plausível."
4. **Abra "Persona e regras" e "Bloco de fatos" na barra lateral.** "A identidade
   do agente é um arquivo de texto, e isto é literalmente o que o modelo recebe.
   Dá para auditar sem abrir o código."
5. **Rode a suíte no terminal:** `python avaliacao/avaliar.py` → 31/31.
   "Teste automático que roda sem LLM nenhum — e seis dessas verificações são
   sobre a própria definição do agente."

### 4. Diferencial e Impacto (30 seg)

> "Três coisas separam esse projeto de um chatbot com prompt bonito.
>
> A primeira é o conflito entre metas — uma informação que não está em nenhum
> arquivo de dados, é calculada, e é a mais útil da tela.
>
> A segunda é que a seleção de produto é uma regra em Python, não uma opinião do
> modelo. Por isso o agente consegue explicar por que um produto **não** apareceu.
>
> A terceira é que a parte perigosa do agente virou software testável. Trinta e
> uma verificações rodando sem modelo nenhum — inclusive uma que falha se alguém
> copiar o system prompt de volta para dentro do código. Prompt reduz a chance de
> erro; arquitetura elimina a categoria. Era isso que eu queria provar."

---

## Checklist do Pitch

- [ ] Abrir pelo conflito entre as metas, não pela tecnologia
- [ ] Dizer o número R$ 311,52 em voz alta — é o que gruda
- [ ] Mostrar o painel **antes** da conversa, para estabelecer que os números não vêm do modelo
- [ ] Demonstrar uma recusa, não só um acerto
- [ ] Mostrar que os botões vêm de arquivos, não do código
- [ ] Rodar a suíte de avaliação ao vivo
- [ ] Fechar com "prompt reduz a chance, arquitetura elimina a categoria"
- [ ] Não passar de 3 minutos — cronometrar no ensaio
- [ ] Fazer uma pergunta de aquecimento antes de gravar, para o cache do prompt já estar quente

## Link do Vídeo

> A gravar. Colar aqui o link do vídeo de até 3 minutos.
