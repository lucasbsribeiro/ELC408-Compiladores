# Trabalho Final - Compiladores (2026)
# Parte 1 - Definicao da Linguagem Homi

## 1. Objetivo da linguagem
A linguagem Homi foi desenhada para permitir que pessoas leigas descrevam automacoes do Home Assistant com poucas palavras, sem precisar conhecer YAML, servicos ou estruturas internas. O foco esta em clareza, previsibilidade e frases curtas, com estrutura fixa.

A linguagem nao pretende substituir todas as possibilidades do Home Assistant. Ela cobre o conjunto mais comum de casos observados em automacoes residenciais:
- movimentos e sensores
- horarios e eventos do sol
- condicoes simples (estado, horario, alarme, clima)
- acoes diretas (ligar, desligar, notificar, esperar)
- ramificacoes condicionais (se / senao) e escolha por casos
- modo de execucao (single/restart/queued/parallel)

## 2. Publico alvo e principios de design
Publico alvo:
- usuarios sem conhecimento tecnico
- usuarios que sabem apenas copiar o entity_id do Home Assistant

Principios adotados:
- Frases curtas e ordem fixa: quando -> se -> entao -> modo
- Palavras simples: quando, se, entao, senao, escolha, caso, esperar
- Uso de aliases para entidades (nome amigavel) em vez de entity_id completo
- Separacao explicita de acoes com ponto e virgula
- Comentarios simples em uma linha

## 3. Conceitos principais
A linguagem trabalha com os seguintes conceitos:
- **Entidade**: item do Home Assistant (luz, sensor, interruptor, alarme, timer, clima, midia, cortina, etc.).
- **Alias**: nome amigavel definido pelo usuario e mapeado para um entity_id real.
- **Gatilho (trigger)**: evento que inicia a automacao (movimento, tempo, sol, mudanca de estado).
- **Condicao**: teste logico que precisa ser verdadeiro para executar as acoes.
- **Acao**: comando executado quando os gatilhos disparam e as condicoes sao verdadeiras.
- **Modo**: comportamento do Home Assistant quando a automacao e disparada novamente.

## 4. Estrutura geral de um programa
Um programa Homi possui duas partes opcionais/obrigatorias:
1) Declaracao de entidades (opcional, mas recomendada)
2) Lista de automacoes (obrigatoria)

Exemplo de forma geral:

```
entidades {
  luz luz_sala = light.luzes_da_sala;
  sensor mov_sala = binary_sensor.sala_motion_sensor;
  alarme casa = alarm_control_panel.alarmo;
}

automacao "Sala - movimento" {
  quando mov_sala muda para on;
  se casa esta desarmado e luz_sala esta desligada;
  entao ligar luz_sala; esperar 3min; desligar luz_sala;
  modo restart;
}
```

## 5. Declaracao de entidades (aliases)
A declaracao de entidades reduz erros e evita que o usuario precise memorizar entity_id. Cada alias possui um tipo e um valor real.

Sintaxe:
```
entidades {
  <tipo> <alias> = <entity_id>;
}
```

Tipos sugeridos (extensivel):
- luz
- sensor
- interruptor
- alarme
- timer
- clima
- midia
- cortina
- cena
- grupo

Regras:
- O alias e unico dentro do programa.
- O entity_id segue o padrao `dominio.nome`.
- O tipo serve para validacao semantica futura (ex: luz so pode receber ligar/desligar).

## 6. Palavras reservadas e simbolos
Palavras reservadas principais:
- automacao, entidades, quando, se, entao, senao, escolha, caso, modo
- e, ou, nao
- ligar, desligar, esperar, notificar
- por_do_sol, nascer_do_sol
- entre, depois, antes, por

Simbolos usados:
- `{ }` bloco
- `( )` agrupamento de condicoes
- `;` fim de acao ou bloco
- `=` atribuicao
- `.` separador de dominio e servico
- `,` separador de argumentos

Comentarios (uma linha):
- `# comentario`
- `// comentario`

## 7. Terminais e nao-terminais (resumo)
Nao-terminais principais:
- <programa>, <bloco_entidades>, <automacao>, <gatilho>, <condicao>, <acao>
- <expr_cond>, <expr_or>, <expr_and>, <expr_not>
- <valor>, <lista>, <mapa>, <args>

Terminais principais:
- KEYWORDS: automacao, entidades, quando, se, entao, senao, escolha, caso, modo, e, ou, nao
- ACTIONS: ligar, desligar, esperar, notificar
- SOL: por_do_sol, nascer_do_sol
- TIPOS: luz, sensor, interruptor, alarme, timer, clima, midia, cortina, cena, grupo
- IDENT, STRING, NUMBER, BOOLEAN, ENTITY_ID, TIME, DURATION

## 8. Gramatica Livre de Contexto (GLC)
A seguir, a gramatica em forma BNF. Ela foi escrita para facilitar a construcao de parser LL(1) na etapa seguinte.

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

<gatilho_estado> ::= <ref_entidade> "muda" "para" <valor_estado> <janela_opt>
<gatilho_evento> ::= "evento" <ident>
<gatilho_tempo> ::= "hora" <hora>
                  | "entre" <hora> "e" <hora>
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

Observacoes de projeto:
- A gramatica separa claramente as fases: quando, se, entao, modo.
- O uso de `;` e obrigatorio para facilitar sincronizacao no modo panico.
- Acoes e listas sao definidas com recursao a direita para facilitar LL(1).

## 9. Exemplos de scripts Homi (apenas ilustrativos)
Os exemplos abaixo sao baseados em automacoes reais do arquivo [automations_homi.yaml](automations_homi.yaml), mas com escrita mais simples para usuarios leigos.

### 9.1 Exemplo: Corredor - movimento
```
entidades {
  sensor mov_corredor = binary_sensor.motion_sensor_movimento;
  luz led_corredor = light.corda_led_corredor;
  alarme casa = alarm_control_panel.alarmo;
}

automacao "Corredor - movimento" {
  quando mov_corredor muda para on;
  se casa esta disarmed e led_corredor esta off;
  entao ligar led_corredor; esperar 45s; desligar led_corredor;
  modo restart;
}
```

### 9.2 Exemplo: Por do sol com clima
```
entidades {
  clima tempo = weather.forecast_casa;
}

automacao "Por do sol" {
  quando por_do_sol -45min;
  se tempo esta cloudy ou tempo esta rainy;
  entao servico automation.trigger(entity_id=automation.cozinha_ligar_luzes, skip_condition=true);
  modo single;
}
```

### 9.3 Exemplo: Porta de entrada aberta
```
entidades {
  sensor porta = binary_sensor.porta_entrada;
  luz entrada = light.luz_entrada;
  midia tv = media_player.music_frame;
}

automacao "Porta de entrada" {
  quando porta muda para on;
  se entrada esta off e tv esta off;
  entao ligar entrada; notificar "Porta aberta e luz ligada";
  modo single;
}
```

## 10. Mapeamento conceitual para YAML (alto nivel)
A linguagem Homi foi planejada para mapear diretamente para o YAML do Home Assistant:
- Cada `automacao` vira um item de lista YAML com `id`, `alias`, `triggers`, `conditions`, `actions` e `mode`.
- O bloco `quando` vira `triggers`.
- O bloco `se` vira `conditions`.
- O bloco `entao` vira `actions`.
- O bloco `modo` vira `mode`.

Este mapeamento sera detalhado na parte de geracao de codigo (etapa D), mas a definicao da linguagem ja foi pensada para manter essa traducao direta.

## 11. Limites assumidos nesta versao
Para manter a linguagem simples para o publico leigo:
- Apenas um bloco `quando` por automacao.
- Apenas um bloco `se` por automacao.
- Acoes em sequencia linear, com opcao de `se/senao` e `escolha`.
- Comentarios apenas de uma linha.
- Tipos de entidades definidos pelo usuario em `entidades`.

Esses limites podem ser expandidos sem quebrar a base da gramatica.
