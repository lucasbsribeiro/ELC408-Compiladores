# Homi — Compilador de automações para Home Assistant

Converte scripts `.homi` em arquivos `automations.yaml` prontos para o Home Assistant.

---

## Como rodar

**Pré-requisito:** Python 3.14+

```bash
python homi.py minha_automacao.homi
```

O arquivo `automations.yaml` será gerado no diretório atual.

### Opções

```bash
python homi.py <arquivo.homi> [opções]

  -o, --output <arquivo>   Arquivo YAML de saída (padrão: automations.yaml)
```

### Exemplos

```bash
# Saída padrão
python homi.py casa.homi

# Saída customizada
python homi.py casa.homi -o config/automations.yaml
```

---

## Estrutura do projeto

```
homi.py               # Ponto de entrada
compiler/
  lexer.py            # Tokenização
  parser.py           # Análise sintática
  ast.py              # Nós da árvore sintática
  semantics.py        # Validação semântica
  generator.py        # Geração do YAML
  yaml_writer.py      # Serialização YAML
```

---

## Sintaxe básica

```homi
entidades {
  luz sala = light.sala_principal;
  sensor temp = sensor.temperatura_sala;
}

automacao "Ligar luz à noite" {
  quando sala muda para ligado
  entao {
    ligar sala;
  }
}
```

### Tipos de entidade suportados
`luz`, `sensor`, `interruptor`, `alarme`, `timer`, `clima`, `midia`, `cortina`, `cena`, `grupo`

### Gatilhos disponíveis
- Estado: `quando <entidade> muda para <estado>`
- Horário: `hora <HH:MM>`
- Intervalo: `entre <HH:MM> e <HH:MM>`
- Solar: `por_do_sol` / `nascer_do_sol`
- Evento: `evento <nome>`
- Dispositivo: `dispositivo <entidade> <evento>`

### Ações disponíveis
- `ligar`/`desligar <entidade>`
- `esperar <duração>` (ex: `30s`, `5min`, `2h`)
- `notificar "<mensagem>"`
- `servico <dominio>.<servico>(...)`
- Condicionais: `se ... entao { ... } senao { ... }`
- Escolha: `escolha { caso ... }`

### Modos de automação
`single` (padrão), `restart`, `queued`, `parallel`

---

## Erros

Erros são exibidos no stderr com categoria e linha:

```
[Lexico] Linha 3, Coluna 12: token invalido '@'
[Sintatico] Linha 7: esperado ';'
[Semantico] Linha 10: alias 'sala' nao declarado
```