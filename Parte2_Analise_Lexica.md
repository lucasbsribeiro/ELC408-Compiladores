# Trabalho Final - Compiladores (2026)
# Parte 2 - Analise Lexica (Scanner)

## 1. Objetivo
A analise lexica (scanner) transforma o texto Homi em uma sequencia de tokens reconheciveis pelo parser. O scanner precisa:
- reconhecer palavras reservadas e simbolos
- reconhecer tokens complexos: `ENTITY_ID`, `TIME`, `DURATION`, `STRING`
- ignorar comentarios e espacos
- contar linhas (e colunas) para erro
- continuar apos erros simples

## 2. Estrategia geral do scanner
- Algoritmo: leitura caractere a caractere, com politica de **maior prefixo** (longest match).
- Apos reconhecer um token, o scanner retorna seu tipo e lexema.
- Palavras reservadas tem precedencia sobre `IDENT`.
- Comentarios sao descartados e nao geram tokens.
- Quebras de linha atualizam o contador de linha.

## 3. Conjunto de caracteres
- Letras: `A-Z`, `a-z`
- Digitos: `0-9`
- Simbolos: `{ } ( ) [ ] = ; , . + - :`
- Operadores compostos: `->`, `<=`, `>=`, `==` (futuro), `!=` (futuro)

## 4. Ignoraveis
- **Whitespace**: `espaco`, `\t`, `\r`, `\n`
- **Comentarios de linha**:
  - `# ...` ate o final da linha
  - `// ...` ate o final da linha

Regra: ao consumir `\n` em comentario ou whitespace, incrementa `linha` e zera `coluna`.

## 5. Tabela de tokens

### 5.1 Palavras reservadas (KEYWORDS)
- `automacao`, `entidades`, `quando`, `se`, `entao`, `senao`, `escolha`, `caso`, `modo`
- `e`, `ou`, `nao`
- `ligar`, `desligar`, `esperar`, `notificar`, `servico`
- `evento`, `dispositivo`, `hora`, `entre`, `depois`, `antes`, `por`
- `por_do_sol`, `nascer_do_sol`

### 5.2 Literais e identificadores
- `IDENT`: nomes de variaveis/aliases
- `ENTITY_ID`: entidade do Home Assistant (ex: `sensor.temperature_living_room`)
- `STRING`: texto entre aspas duplas
- `NUMBER`: inteiro ou decimal
- `BOOLEAN`: `true`, `false`
- `STATE`: estados comuns (`on`, `off`, `disarmed`, `armed`, `idle`, `active`, `charging`, `running`, `standby`, `playing`)

### 5.3 Simbolos e operadores
- `LBRACE` `{`  | `RBRACE` `}`
- `LPAREN` `(`  | `RPAREN` `)`
- `LBRACKET` `[` | `RBRACKET` `]`
- `ASSIGN` `=`
- `SEMICOLON` `;`
- `COMMA` `,`
- `DOT` `.`
- `COLON` `:`
- `ARROW` `->`
- `PLUS` `+` | `MINUS` `-`

### 5.4 Tempo e duracao
- `TIME`: `HH:MM` ou `HH:MM:SS`
- `DURATION`: `<numero><unidade>`
  - unidades: `ms`, `s`, `min`, `h`, `d`
  - exemplos: `45s`, `5min`, `1h`

## 6. Regras lexicas (regex)
Notacao simplificada de regex:

- `LETTER` = `[A-Za-z]`
- `DIGIT` = `[0-9]`

- `IDENT` = `LETTER (LETTER | DIGIT | _)*`
- `ENTITY_ID` = `[a-z_][a-z0-9_]*\.[a-z0-9_]+`

- `NUMBER` = `DIGIT+ ('.' DIGIT+)?`
- `BOOLEAN` = `true | false`

- `TIME` = `([01]?[0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9])?`
- `DURATION` = `NUMBER (ms|s|min|h|d)`

- `STRING` = `" (\\.|[^"\\])* "`
  - permite escape: `\"`, `\\`, `\n`, `\t`

### 6.1 Prioridade de reconhecimento
1) Comentarios
2) Palavras reservadas
3) `DURATION` (ex: `10s`) antes de `NUMBER`
4) `TIME` (ex: `23:59`) antes de `NUMBER`
5) `ENTITY_ID` antes de `IDENT`
6) `IDENT`
7) Simbolos

## 7. Regra especial: ENTITY_ID vs servico
Para evitar confusao entre `entity_id` e `servico`, usa-se um pequeno contexto:
- Se o ultimo token significativo for `servico`, entao a sequencia `ident . ident` deve ser tokenizada como `IDENT`, `DOT`, `IDENT`.
- Fora desse contexto, a mesma sequencia pode ser tokenizada como `ENTITY_ID`.

Isso permite manter o parser simples e atender o requisito de `ENTITY_ID` como token complexo.

## 8. Descricao do DFA (alto nivel)
O DFA pode ser descrito por estados principais:

- `S0` (inicio)
  - letra -> `S_ID`
  - digito -> `S_NUM`
  - `"` -> `S_STRING`
  - `#` -> `S_COMMENT`
  - `/` seguido de `/` -> `S_COMMENT`
  - simbolo simples -> token imediato
  - `-` seguido de `>` -> `ARROW`

- `S_ID` (identificador/palavra reservada)
  - continua enquanto `LETTER|DIGIT|_`
  - se encontra `.` e nao esta em modo `servico`, tenta formar `ENTITY_ID`
  - senao encerra e valida palavra reservada

- `S_NUM` (numero/tempo/duracao)
  - consome digitos
  - se encontrar `:` -> tenta `TIME`
  - se encontrar `.` -> continua decimal
  - se encontrar letras `ms|s|min|h|d` -> `DURATION`

- `S_STRING`
  - consome ate `"` nao escapado
  - reconhece escapes (`\n`, `\t`, `\"`, `\\`)

- `S_COMMENT`
  - consome ate `\n`

Estados de erro:
- caractere desconhecido
- string nao terminada
- tempo invalido (ex: `25:99`)
- duracao invalida (ex: `10x`)

## 9. Tratamento de erros lexicos
Regras de recuperacao:
- Se um caractere e invalido: gera token `ERROR` e avanca 1 char.
- Se uma string nao fecha: reporta erro, descarta ate o fim da linha.
- Se um numero/tempo e invalido: reporta erro e tenta continuar apos o token.

Formato de erro sugerido:
```
[Lexico] Linha 12, Coluna 8: token invalido '@'
```

## 10. Exemplos de tokenizacao

Entrada:
```
automacao "Sala - movimento" {
  quando mov_sala muda para on;
  se hora entre 01:00 e 06:30;
  entao ligar luz_sala; esperar 45s; desligar luz_sala;
  modo restart;
}
```

Saida (sequencia de tokens):
```
AUTOMACAO STRING LBRACE
QUANDO IDENT IDENT IDENT STATE SEMICOLON
SE HORA ENTRE TIME E TIME SEMICOLON
ENTAO LIGAR IDENT SEMICOLON ESPERAR DURATION SEMICOLON DESLIGAR IDENT SEMICOLON
MODO IDENT SEMICOLON
RBRACE
```

## 11. Relacao com o YAML de base
O arquivo de referencia [automations_homi.yaml](automations_homi.yaml) mostra os valores reais de `ENTITY_ID` e `STATE` usados nas automacoes. Esses valores orientam os exemplos e o conjunto de estados reconhecidos.

## 12. Saidas esperadas do scanner
O scanner deve produzir:
- lista de tokens (`tipo`, `lexema`, `linha`, `coluna`)
- lista de erros lexicos

Essas saidas alimentam a etapa sintatica (Parte 3).
