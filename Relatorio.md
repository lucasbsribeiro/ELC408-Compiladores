# Relatorio - Homi Compiler

## 1. Objetivo
A linguagem Homi foi criada para permitir que usuarios descrevam automacoes do Home Assistant com frases simples, evitando o YAML. O compilador recebe arquivos .homi, valida o conteudo (lexico, sintatico e semantico) e gera um YAML valido.

## 2. Gramatica (BNF)
A gramatica foi definida para permitir analise top-down com 1 token de lookahead (LL(1)).

```
<programa> ::= <bloco_entidades_opt> <lista_automacoes>

<bloco_entidades_opt> ::= <bloco_entidades> | epsilon
<bloco_entidades> ::= "entidades" "{" <lista_declaracoes> "}"
<lista_declaracoes> ::= <declaracao> <lista_declaracoes> | epsilon
<declaracao> ::= <tipo_entidade> <ident> "=" <entity_id> ";"

<lista_automacoes> ::= <automacao> <lista_automacoes> | epsilon
<automacao> ::= "automacao" <string> "{" <corpo_automacao> "}"
<corpo_automacao> ::= <bloco_quando> <bloco_se_opt> <bloco_entao> <bloco_modo_opt>

<bloco_quando> ::= "quando" <lista_gatilhos> ";"
<lista_gatilhos> ::= <gatilho> <lista_gatilhos_tail>
<lista_gatilhos_tail> ::= "ou" <gatilho> <lista_gatilhos_tail> | epsilon

<gatilho> ::= <gatilho_estado>
           | <gatilho_evento>
           | <gatilho_tempo>
           | <gatilho_sol>
           | <gatilho_dispositivo>
           | <gatilho_entre>

<gatilho_estado> ::= <ref_entidade> "muda" "para" <valor_estado> <janela_opt>
<gatilho_evento> ::= "evento" <ident>
<gatilho_tempo> ::= "hora" <hora>
<gatilho_entre> ::= "entre" <hora> "e" <hora>
<gatilho_sol> ::= "por_do_sol" <offset_opt>
                | "nascer_do_sol" <offset_opt>
<gatilho_dispositivo> ::= "dispositivo" <ref_entidade> <evento_dispositivo> <janela_opt>

<janela_opt> ::= "por" <duracao> | epsilon
<offset_opt> ::= "+" <duracao> | "-" <duracao> | epsilon

<bloco_se_opt> ::= <bloco_se> | epsilon
<bloco_se> ::= "se" <expr_cond> ";"

<expr_cond> ::= <expr_or>
<expr_or> ::= <expr_and> <expr_or_tail>
<expr_or_tail> ::= "ou" <expr_and> <expr_or_tail> | epsilon
<expr_and> ::= <expr_not> <expr_and_tail>
<expr_and_tail> ::= "e" <expr_not> <expr_and_tail> | epsilon
<expr_not> ::= "nao" <expr_not> | <prim_cond>
<prim_cond> ::= "(" <expr_cond> ")" | <condicao>

<condicao> ::= <condicao_estado>
             | <condicao_tempo>
             | <condicao_sol>
             | <condicao_dispositivo>

<condicao_estado> ::= <ref_entidade> "esta" <valor_estado>
<condicao_tempo> ::= "hora" "entre" <hora> "e" <hora>
                   | "hora" "depois" <hora>
                   | "hora" "antes" <hora>
<condicao_sol> ::= "sol" "entre" "por_do_sol" "e" "nascer_do_sol"
<condicao_dispositivo> ::= "dispositivo" <ref_entidade> "esta" <valor_estado>

<bloco_entao> ::= "entao" <lista_acoes> ";"
<lista_acoes> ::= <acao> <lista_acoes_tail>
<lista_acoes_tail> ::= ";" <acao> <lista_acoes_tail> | epsilon

<acao> ::= <acao_ligar>
         | <acao_desligar>
         | <acao_esperar>
         | <acao_notificar>
         | <acao_timer>
         | <acao_servico>
         | <acao_se>
         | <acao_escolha>

<acao_ligar> ::= "ligar" <ref_entidade>
<acao_desligar> ::= "desligar" <ref_entidade>
<acao_esperar> ::= "esperar" <duracao>
<acao_notificar> ::= "notificar" <string>
<acao_timer> ::= "timer" <ref_entidade> <acao_timer_tipo>
<acao_timer_tipo> ::= "iniciar" | "parar" | "finalizar"

<acao_servico> ::= "servico" <ident> "." <ident> "(" <args_opt> ")"
<args_opt> ::= <args> | epsilon
<args> ::= <arg> <args_tail>
<args_tail> ::= "," <arg> <args_tail> | epsilon
<arg> ::= <ident> "=" <valor>

<acao_se> ::= "se" <expr_cond> "entao" <lista_acoes>
            | "se" <expr_cond> "entao" <lista_acoes> "senao" <lista_acoes>

<acao_escolha> ::= "escolha" "{" <lista_casos> <senao_opt> "}"
<lista_casos> ::= <caso> <lista_casos> | epsilon
<caso> ::= "caso" <expr_cond> "->" <lista_acoes> ";"
<senao_opt> ::= "senao" <lista_acoes> ";" | epsilon

<bloco_modo_opt> ::= <bloco_modo> | epsilon
<bloco_modo> ::= "modo" <modo> ";"
<modo> ::= "single" | "restart" | "queued" | "parallel"

<ref_entidade> ::= <ident> | <entity_id>

<valor> ::= <string> | <numero> | <booleano> | <duracao> | <ref_entidade> | <lista> | <mapa>
<lista> ::= "[" <lista_valores_opt> "]"
<lista_valores_opt> ::= <valor> <lista_valores_tail> | epsilon
<lista_valores_tail> ::= "," <valor> <lista_valores_tail> | epsilon
<mapa> ::= "{" <mapa_itens_opt> "}"
<mapa_itens_opt> ::= <mapa_item> <mapa_itens_tail> | epsilon
<mapa_itens_tail> ::= "," <mapa_item> <mapa_itens_tail> | epsilon
<mapa_item> ::= <ident> ":" <valor>

<valor_estado> ::= "on" | "off" | "disarmed" | "armed" | <string> | <numero>

<hora> ::= <TIME>
<duracao> ::= <NUMBER> <UNIDADE>

<tipo_entidade> ::= "luz" | "sensor" | "interruptor" | "alarme" | "timer" | "clima" | "midia" | "cortina" | "cena" | "grupo"

<ident> ::= <IDENT>
<string> ::= <STRING>
<numero> ::= <NUMBER>
<booleano> ::= "true" | "false"
<entity_id> ::= <ENTITY_ID>
```

## 3. Ferramentas e instalacao
Requisitos:
- Python 3.10+ instalado e no PATH.
- Nenhuma dependencia externa.

Passos (Windows):
1) Instale o Python em https://www.python.org/ (marque "Add Python to PATH").
2) Abra o terminal e valide: `python --version`.
3) Navegue ate a pasta do projeto.

Passos (Linux/macOS):
1) Instale Python 3.10+ pelo gerenciador de pacotes.
2) Valide: `python3 --version`.

## 4. Como executar
Comando principal:
```
python homi.py exemplos\exemplo.homi -o automations.yaml
```
Para gerar mesmo com erros:
```
python homi.py exemplos\exemplo.homi -o automations.yaml --force
```

## 5. Implementacao
### 5.1 Analise Lexica (Scanner)
- Arquivo: compiler/lexer.py
- Reconhecimento por maior prefixo (regex para TIME, DURATION e NUMBER).
- Palavras reservadas e tipos sao priorizados antes de IDENT.
- Comentarios (# e //) sao ignorados.
- Contagem de linha e coluna para erros.
- Regra especial apos "servico" para evitar confusao entre ENTITY_ID e dominio.servico.
- Recuperacao: token invalido gera erro e o scanner avanca 1 caractere.

### 5.2 Analise Sintatica (Parser LL(1))
- Arquivo: compiler/parser.py
- Parser top-down com 1 token de lookahead (LL(1)) e funcoes por nao-terminal.
- Uso de conjuntos de sincronizacao e modo panico para recuperar erros.
- A AST e criada durante a analise (nos em compiler/ast.py).

### 5.3 Analise Semantica
- Arquivo: compiler/semantics.py
- Tabela de simbolos com alias, tipo e entity_id.
- Verifica duplicidade de alias e compatibilidade tipo/domino.
- Valida estados por tipo e uso correto de acoes (ligar/desligar, timer, servico).
- Catalogo minimo de servicos validos para a acao "servico".

### 5.4 Geracao de YAML
- Arquivos: compiler/generator.py e compiler/yaml_writer.py
- Conversao direta da AST para estrutura YAML do Home Assistant.
- Normalizacao de estados e horarios, e conversao de duracoes.
- Suporte a choose/if e listas de condicoes.

## 6. Estrutura do projeto
- homi.py: CLI do compilador.
- compiler/: lexer, parser, semantica, gerador e AST.
- exemplos/: scripts .homi validos.

## 7. Exemplos
Os exemplos validos ficam em exemplos/:
- exemplo.homi
- exemplo_timer_servico.homi
- exemplo_condicoes.homi
- exemplo_escolha_if.homi
- exemplo_dispositivo_evento.homi

## 8. Como gerar o PDF
Abra este arquivo (Relatorio.md) no VS Code e exporte para PDF usando a opcao de impressao do editor (Print -> Save as PDF) ou um gerador de Markdown para PDF (ex: pandoc).
