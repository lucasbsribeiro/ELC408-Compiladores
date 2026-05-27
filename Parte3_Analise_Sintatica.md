# Trabalho Final - Compiladores (2026)
# Parte 3 - Analise Sintatica (Parser Top-Down LL(1))

## 1. Objetivo
A analise sintatica valida a estrutura dos scripts Homi e construi a arvore sintatica (AST). Esta parte segue o requisito do trabalho:
- Parser Top-Down LL(1)
- Implementacao baseada em tabela preditiva
- Recuperacao de erros com Modo Panico

## 2. Forma da GLC
A gramatica apresentada na Parte 1 foi escrita para ser LL(1) com recursao a direita e fatores claros.
Nesta parte, assumimos a mesma GLC, com pequenas normalizacoes para facilitar a tabela preditiva:
- uso de nao-terminais auxiliares para listas (`<lista_x_tail>`)
- eliminacao de recursao a esquerda
- fatoracao de opcoes comuns

O parser trabalha sobre a GLC de [Parte1_Definicao_Linguagem_Homi.md](Parte1_Definicao_Linguagem_Homi.md).

## 3. Entrada e saida do parser
Entrada:
- Sequencia de tokens do scanner (tipo, lexema, linha, coluna).

Saida:
- AST (nos para automacao, gatilhos, condicoes, acoes, etc.)
- Lista de erros sintaticos

## 4. Conjunto de simbolos
Nao-terminais (principais):
- <programa>, <bloco_entidades_opt>, <lista_automacoes>
- <automacao>, <corpo_automacao>, <bloco_quando>, <bloco_se_opt>, <bloco_entao>, <bloco_modo_opt>
- <gatilho>, <condicao>, <expr_cond>, <lista_acoes>

Terminais (resumo):
- KEYWORDS (automacao, entidades, quando, se, entao, senao, escolha, caso, modo, etc.)
- IDENT, STRING, NUMBER, BOOLEAN, ENTITY_ID, TIME, DURATION
- simbolos: `{ } ( ) [ ] = ; , . : -> + -`

## 5. FIRST e FOLLOW (amostras)
Para demonstrar LL(1), listamos FIRST/FOLLOW de nao-terminais criticos:

FIRST(<programa>) = { entidades, automacao, epsilon }
FOLLOW(<programa>) = { EOF }

FIRST(<bloco_entidades_opt>) = { entidades, epsilon }
FOLLOW(<bloco_entidades_opt>) = { automacao, EOF }

FIRST(<automacao>) = { automacao }
FOLLOW(<automacao>) = { automacao, EOF }

FIRST(<bloco_quando>) = { quando }
FOLLOW(<bloco_quando>) = { se, entao }

FIRST(<bloco_se_opt>) = { se, epsilon }
FOLLOW(<bloco_se_opt>) = { entao }

FIRST(<bloco_entao>) = { entao }
FOLLOW(<bloco_entao>) = { modo, RBRACE }

FIRST(<bloco_modo_opt>) = { modo, epsilon }
FOLLOW(<bloco_modo_opt>) = { RBRACE }

FIRST(<gatilho>) = { IDENT, ENTITY_ID, evento, hora, entre, por_do_sol, nascer_do_sol, dispositivo }

FIRST(<acao>) = { ligar, desligar, esperar, notificar, timer, servico, se, escolha }

Observacao: o token IDENT pode iniciar varios nao-terminais. A tabela preditiva resolve usando o simbolo seguinte (lookahead).

## 6. Tabela preditiva LL(1) (recorte)
A tabela completa pode ser grande. Abaixo um recorte do bloco principal, suficiente para implementar o parser:

```
M[<programa>, entidades] = <bloco_entidades_opt> <lista_automacoes>
M[<programa>, automacao] = <bloco_entidades_opt> <lista_automacoes>
M[<programa>, EOF] = <bloco_entidades_opt> <lista_automacoes>

M[<bloco_entidades_opt>, entidades] = <bloco_entidades>
M[<bloco_entidades_opt>, automacao] = epsilon
M[<bloco_entidades_opt>, EOF] = epsilon

M[<lista_automacoes>, automacao] = <automacao> <lista_automacoes>
M[<lista_automacoes>, EOF] = epsilon

M[<automacao>, automacao] = "automacao" <string> "{" <corpo_automacao> "}"

M[<corpo_automacao>, quando] = <bloco_quando> <bloco_se_opt> <bloco_entao> <bloco_modo_opt>

M[<bloco_quando>, quando] = "quando" <lista_gatilhos> ";"

M[<bloco_se_opt>, se] = <bloco_se>
M[<bloco_se_opt>, entao] = epsilon

M[<bloco_entao>, entao] = "entao" <lista_acoes> ";"

M[<bloco_modo_opt>, modo] = <bloco_modo>
M[<bloco_modo_opt>, RBRACE] = epsilon
```

Para os demais nao-terminais, a tabela e gerada pelas regras da GLC.

## 7. Algoritmo do parser (LL(1))
Pseudo-algoritmo:

```
stack = [EOF, <programa>]
lookahead = next_token()

while top(stack) != EOF:
  X = top(stack)
  if X e terminal:
    if X == lookahead.tipo:
      pop(stack)
      lookahead = next_token()
    else:
      erro("token inesperado")
      lookahead = next_token()  # recovery simples
  else:
    if M[X, lookahead.tipo] existe:
      pop(stack)
      push producao M[X, lookahead.tipo] (em ordem reversa)
    else:
      erro("sincronizacao")
      modo_panico(X)
```

## 8. Recuperacao de erros (Modo Panico)
Requisito: o parser nao pode abortar no primeiro erro.

Estrategia:
- Para cada nao-terminal X, define-se um conjunto de sincronizacao (SYNC):
  - SYNC(X) = FOLLOW(X) + tokens delimitadores (ex: `;`, `}`)
- Em erro de tabela (M[X, a] vazio):
  - reporta erro
  - descarta tokens ate encontrar um token em SYNC(X)
  - se o token for de FOLLOW(X), faz `pop(X)` e continua

Exemplos de SYNC:
- SYNC(<bloco_quando>) = { se, entao, RBRACE, SEMICOLON }
- SYNC(<bloco_se>) = { entao, RBRACE, SEMICOLON }
- SYNC(<lista_acoes>) = { modo, RBRACE, SEMICOLON }

## 9. Erros tipicos e mensagens
- Token inesperado:
  - "[Sintatico] Linha 10: esperado 'entao', encontrado 'modo'"
- Falta de delimitador:
  - "[Sintatico] Linha 22: esperado ';' apos acao"
- Fechamento de bloco ausente:
  - "[Sintatico] Linha 30: esperado '}'"

## 10. Relacao com a AST
O parser constroi nos principais:
- `ProgramNode`
- `AutomationNode`
- `TriggerNode`, `ConditionNode`, `ActionNode`
- `IfNode`, `ChooseNode`

Cada producao principal adiciona um no a AST. Exemplo:
- Ao reduzir `<automacao>`, cria `AutomationNode` com alias, gatilhos, condicoes, acoes e modo.

## 11. Exemplo de analise (resumo)
Entrada:
```
automacao "Sala - movimento" {
  quando mov_sala muda para on;
  se hora entre 01:00 e 06:30;
  entao ligar luz_sala; esperar 45s; desligar luz_sala;
  modo restart;
}
```

O parser reconhece a sequencia de producoes:
- <programa> -> <lista_automacoes>
- <automacao> -> automacao string { <corpo_automacao> }
- <corpo_automacao> -> <bloco_quando> <bloco_se_opt> <bloco_entao> <bloco_modo_opt>
- ...

## 12. Saidas esperadas
- AST valida
- Lista de erros com linha/coluna

Essas saidas alimentam a etapa semantica (Parte 4).
