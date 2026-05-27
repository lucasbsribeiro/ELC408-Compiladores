# Trabalho Final - Compiladores (2026)
# Parte 5 - Geracao de Codigo (YAML do Home Assistant)

## 1. Objetivo
A geracao de codigo transforma a AST validada em YAML no formato esperado pelo Home Assistant, preservando a semantica de gatilhos, condicoes e acoes.

Requisitos atendidos:
- Traducao da AST para estrutura declarativa
- Indentacao rigida do YAML
- Mapeamento de triggers, conditions e actions

## 2. Estrutura alvo no YAML
Cada automacao vira um item de lista com esta estrutura:
```
- id: '<id_gerado>'
  alias: <nome>
  description: ''
  triggers: [ ... ]
  conditions: [ ... ]
  actions: [ ... ]
  mode: <modo>
```

Campos:
- `id`: string unica gerada pelo compilador
- `alias`: nome da automacao (string)
- `description`: vazio por padrao
- `triggers`: lista de gatilhos
- `conditions`: lista de condicoes
- `actions`: lista de acoes
- `mode`: `single`, `restart`, `queued`, `parallel`

## 3. Regras de geracao

### 3.1 Geracao de id
- Regra simples: timestamp ou contador incremental
- Exemplo: `id = "1700000000000"`

### 3.2 Declaracoes de entidades
- As declaracoes `entidades` nao geram YAML
- Elas apenas alimentam a tabela de simbolos

### 3.3 Gatilhos

#### Gatilho de estado
Homi:
```
quando luz_sala muda para on;
```
YAML:
```
- trigger: state
  entity_id: light.luzes_da_sala
  to: 'on'
```

#### Gatilho com janela de tempo
Homi:
```
quando porta muda para on por 1min;
```
YAML:
```
- trigger: state
  entity_id: binary_sensor.porta
  to: 'on'
  for:
    minutes: 1
```

#### Gatilho de tempo
Homi:
```
quando hora 23:00;
```
YAML:
```
- trigger: time
  at: '23:00:00'
```

#### Gatilho entre horarios
Homi:
```
quando entre 01:00 e 06:30;
```
YAML (condicao equivalente):
```
- trigger: time
  at: '01:00:00'
```
Observacao: o Home Assistant nao possui trigger direto "entre", entao a pratica e converter para condicao de tempo. O gatilho pode ser um horario especifico ou evento externo.

#### Gatilho do sol
Homi:
```
quando por_do_sol -45min;
```
YAML:
```
- trigger: sun
  event: sunset
  offset: -00:45:00
```

### 3.4 Condicoes

#### Condicao de estado
Homi:
```
se luz_sala esta off;
```
YAML:
```
- condition: state
  entity_id: light.luzes_da_sala
  state: 'off'
```

#### Condicao de tempo
Homi:
```
se hora entre 01:00 e 06:30;
```
YAML:
```
- condition: time
  after: '01:00:00'
  before: '06:30:00'
```

#### Condicao do sol
Homi:
```
se sol entre por_do_sol e nascer_do_sol;
```
YAML:
```
- condition: sun
  before: sunrise
  after: sunset
```

### 3.5 Acoes

#### Ligar / desligar
Homi:
```
ligar luz_sala;
```
YAML:
```
- action: light.turn_on
  target:
    entity_id: light.luzes_da_sala
```

Homi:
```
desligar interruptor_som;
```
YAML:
```
- action: switch.turn_off
  target:
    entity_id: switch.som
```

#### Esperar
Homi:
```
esperar 45s;
```
YAML:
```
- delay:
    seconds: 45
```

#### Notificar
Homi:
```
notificar "Porta aberta";
```
YAML:
```
- action: notify.notify
  data:
    message: "Porta aberta"
```

#### Timer
Homi:
```
timer timer_sala iniciar;
```
YAML:
```
- action: timer.start
  target:
    entity_id: timer.sala
```

#### Servico generico
Homi:
```
servico automation.trigger(entity_id=automation.cozinha_ligar_luzes, skip_condition=true);
```
YAML:
```
- action: automation.trigger
  target:
    entity_id: automation.cozinha_ligar_luzes
  data:
    skip_condition: true
```

### 3.6 Se/Senao
Homi:
```
se condicao entao ligar luz_sala; senao desligar luz_sala;
```
YAML:
```
- if:
    - condition: state
      entity_id: light.luzes_da_sala
      state: 'on'
  then:
    - action: light.turn_on
      target:
        entity_id: light.luzes_da_sala
  else:
    - action: light.turn_off
      target:
        entity_id: light.luzes_da_sala
```

### 3.7 Escolha (choose)
Homi:
```
escolha {
  caso tempo esta rainy -> ligar luz_sala;
  caso tempo esta cloudy -> ligar luz_sala;
  senao desligar luz_sala;
}
```
YAML:
```
- choose:
  - conditions:
      - condition: state
        entity_id: weather.forecast_casa
        state: rainy
    sequence:
      - action: light.turn_on
        target:
          entity_id: light.luzes_da_sala
  - conditions:
      - condition: state
        entity_id: weather.forecast_casa
        state: cloudy
    sequence:
      - action: light.turn_on
        target:
          entity_id: light.luzes_da_sala
  default:
    - action: light.turn_off
      target:
        entity_id: light.luzes_da_sala
```

## 4. Indentacao e formato
- YAML usa 2 espacos por nivel
- Listas com `-` e conteudo indentado
- Strings com espacos devem usar aspas

## 5. Exemplo completo
Entrada Homi:
```
automacao "Corredor - movimento" {
  quando mov_corredor muda para on;
  se casa esta disarmed e luz_corredor esta off;
  entao ligar luz_corredor; esperar 45s; desligar luz_corredor;
  modo restart;
}
```

Saida YAML:
```
- id: '1700000000001'
  alias: Corredor - movimento
  description: ''
  triggers:
  - trigger: state
    entity_id: binary_sensor.motion_sensor_movimento
    to: 'on'
  conditions:
  - condition: state
    entity_id: alarm_control_panel.alarmo
    state: disarmed
  - condition: state
    entity_id: light.corda_led_corredor
    state: 'off'
  actions:
  - action: light.turn_on
    target:
      entity_id: light.corda_led_corredor
  - delay:
      seconds: 45
  - action: light.turn_off
    target:
      entity_id: light.corda_led_corredor
  mode: restart
```

## 6. Observacoes finais
- A geracao de YAML e direta porque a linguagem foi pensada para esse mapeamento.
- A conversao de `entity_id` via alias ocorre aqui.
- Em casos ambigulos (ex: `entre` em gatilhos), a geracao usa a solucao mais simples e valida no HA (ex: converter para condicao).

Com esta parte, o compilador conclui o front-end (lexico, sintatico, semantico) e inicia o back-end (geracao de codigo).