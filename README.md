# Homi Compiler

Compilador didatico para a linguagem Homi, gerando YAML do Home Assistant.

## Requisitos
- Python 3.10+ (sem dependencias externas)

## Como usar

### Windows (cmd/powershell)

```
python homi.py exemplos\exemplo.homi -o automations.yaml
```

Ou usando o atalho:

```
.\homi.bat exemplos\exemplo.homi -o automations.yaml
```

### Linux/macOS

```
python3 homi.py exemplos/exemplo.homi -o automations.yaml
```

## Saida
O compilador cria o arquivo YAML no caminho indicado.
Se houver erros lexicos/sintaticos/semanticos, eles sao listados no terminal.

Para gerar YAML mesmo com erros, use:

```
python homi.py exemplos\exemplo.homi -o automations.yaml --force
```

## Exemplo
O arquivo [exemplos/exemplo.homi](exemplos/exemplo.homi) ja contem um script valido.

## Estrutura do projeto
- homi.py: CLI do compilador
- compiler/: modulos do compilador
- exemplos/: arquivos de entrada Homi
