# Comandos prontos

Cada arquivo `.md` desta pasta é **um comando chamável** do Rumo. O app carrega
todos em tempo de execução (`src/agente.py`) e desenha um botão para cada um; a
lista de sugestões na tela não é escrita no código, ela é esta pasta.

Adicionar um comando = criar um arquivo aqui. Não é preciso mexer em Python.

## Formato

```markdown
---
comando: identificador-em-kebab-case
titulo: O texto do botão
quando: Em que situação esse comando serve
skills: skills usadas, separadas por vírgula
---

## Pergunta

> O texto exato enviado ao agente.
> Pode ter várias linhas.

## O que uma boa resposta faz

- critérios usados na avaliação humana (docs/04-metricas.md)
```

Só o bloco `## Pergunta` vai para o modelo. O resto é para quem lê o repositório
e para a avaliação.
