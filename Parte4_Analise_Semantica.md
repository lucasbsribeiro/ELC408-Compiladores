# Trabalho Final - Compiladores (2026)
# Parte 4 - Analise Semantica

## 1. Objetivo
A analise semantica garante que o script Homi, mesmo sintaticamente correto, faca sentido no dominio do Home Assistant. Esta etapa implementa:
- Tabela de simbolos (tipos de entidades e escopos)
- Verificacao de tipos
- Consistencia externa (servicos compativeis com dominios)

## 2. Estruturas de dados

### 2.1 Tabela de simbolos
Cada alias declarado em `entidades` e armazenado com:
- nome (alias)
- tipo (luz, sensor, interruptor, alarme, timer, clima, midia, cortina, etc.)
- entity_id real
- escopo (global, por enquanto)

Exemplo:
```
Alias: luz_sala
Tipo: luz
EntityId: light.luzes_da_sala
Escopo: global
```

### 2.2 Registro de entidade conhecida
Para validacao externa, o compilador pode manter um catalogo minimo de dominios e servicos validos:
- Dominio `light`: servicos `turn_on`, `turn_off`, `toggle`
- Dominio `switch`: servicos `turn_on`, `turn_off`, `toggle`
- Dominio `timer`: servicos `start`, `finish`, `cancel`
- Dominio `media_player`: servicos `play_media`, `turn_off`, `volume_set`
- Dominio `automation`: servicos `trigger`

Esse catalogo pode ser extendido depois.

## 3. Regras semanticas

### 3.1 Declaracoes
- `alias` nao pode ser duplicado.
- `entity_id` precisa respeitar o padrao `dominio.nome`.
- O dominio do `entity_id` deve ser compativel com o tipo declarado.
  - Ex: `luz minha_luz = light.sala;` OK
  - Ex: `luz minha_luz = sensor.temp;` ERRO

### 3.2 Uso de entidades
- Toda referencia a alias deve existir na tabela de simbolos.
- Se o usuario usar um `ENTITY_ID` direto, ele e aceito, mas o tipo sera inferido pelo dominio.

### 3.3 Tipos de estado
Estados validos variam por dominio:
- luz/interruptor: `on`, `off`
- alarme: `disarmed`, `armed`
- timer: `idle`, `active`
- midia: `off`, `on`, `playing`, `standby`
- sensor: valores numericos ou strings

Regra:
- condicoes e gatilhos de estado devem usar valores compatíveis com o tipo.

Exemplos:
- `se luz_sala esta 25` -> ERRO (luz nao aceita numero)
- `se sensor_temp esta 25` -> OK (sensor aceita numero)

### 3.4 Duracoes e horarios
- `TIME` so pode ser usado em condicoes/gatilhos de tempo.
- `DURATION` so pode ser usado em `esperar`, `por` (janela), ou offsets do sol.

### 3.5 Acoes
- `ligar` e `desligar` somente para `luz`, `interruptor`, `cortina`, `midia`.
- `timer iniciar/parar/finalizar` somente para `timer`.
- `notificar` aceita apenas `STRING`.

### 3.6 Servicos (acao servico)
Formato:
```
servico <dominio>.<servico>(args)
```
Regras:
- dominio deve existir no catalogo.
- servico deve existir para o dominio.
- se houver `entity_id` em args, validar dominio compativel.

### 3.7 Consistencia externa
- `automation.trigger` deve receber `entity_id` de dominio `automation`.
- `light.turn_on` deve receber entidades `light`.

## 4. Algoritmo semantico (passos)
1) Percorrer declaracoes de `entidades` e preencher tabela de simbolos.
2) Percorrer cada automacao:
   - validar gatilhos
   - validar condicoes
   - validar acoes
3) Acumular erros semanticos e continuar.

## 5. Erros semanticos e mensagens
Exemplos de mensagens:
- "[Semantico] Linha 7: alias 'luz_sala' nao declarado"
- "[Semantico] Linha 12: estado '25' invalido para tipo 'luz'"
- "[Semantico] Linha 18: servico 'turn_on' nao existe em dominio 'weather'"

## 6. Exemplos de validacao

### 6.1 Exemplo invalido
```
se luz_sala esta 25;
```
Erro:
```
[Semantico] Linha X: luz_sala (luz) nao aceita valor numerico
```

### 6.2 Exemplo valido
```
se sensor_temp esta 25;
```

## 7. Saida da etapa
- AST validada semanticamente
- Lista de erros semanticos (sem abortar no primeiro erro)

Essa etapa prepara a AST para a geracao de YAML (Parte 5).
