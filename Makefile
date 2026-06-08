# Makefile para compilador Homi com estrutura de pastas:
# exemplos/input/validos/*.homi -> YAML em exemplos/output/validos/
# exemplos/input/invalidos/*.homi -> execução para ver erros (sem gerar YAML)

COMPILER = python -m homi.main   # ajuste conforme seu módulo
INPUT_VALIDOS = exemplos/input/validos
OUTPUT_VALIDOS = exemplos/output/validos
INPUT_INVALIDOS = exemplos/input/invalidos
OUTPUT_INVALIDOS = exemplos/output/invalidos

# Lista de arquivos válidos
VALIDOS = $(wildcard $(INPUT_VALIDOS)/*.homi)
INVALIDOS = $(wildcard $(INPUT_INVALIDOS)/*.homi)

# Alvo padrão: compilar todos os válidos
all: $(patsubst $(INPUT_VALIDOS)/%.homi, $(OUTPUT_VALIDOS)/%.yaml, $(VALIDOS))

# Regra para compilar um arquivo válido em YAML
$(OUTPUT_VALIDOS)/%.yaml: $(INPUT_VALIDOS)/%.homi
	@mkdir -p $(OUTPUT_VALIDOS)
	$(COMPILER) $< > $@

# Executar todos os inválidos (mostra erros no terminal)
invalidos: $(INVALIDOS)
	@for f in $(INVALIDOS); do \
		echo "\n>>> Testando $$f (esperado erro)"; \
		$(COMPILER) $$f; \
	done

# Testar um arquivo específico (válido ou inválido) - exemplo: make test VALIDO=meu_arquivo
test_valid:
	@if [ -z "$(ARQ)" ]; then echo "Uso: make test_valid ARQ=nome_sem_extensao"; exit 1; fi
	$(COMPILER) $(INPUT_VALIDOS)/$(ARQ).homi > $(OUTPUT_VALIDOS)/$(ARQ).yaml

test_invalid:
	@if [ -z "$(ARQ)" ]; then echo "Uso: make test_invalid ARQ=nome_sem_extensao"; exit 1; fi
	$(COMPILER) $(INPUT_INVALIDOS)/$(ARQ).homi

# Teste rápido (mostra saída no terminal, sem salvar)
run:
	@if [ -z "$(ARQ)" ]; then echo "Uso: make run ARQ=caminho/arquivo.homi"; exit 1; fi
	$(COMPILER) $(ARQ)

# Limpeza
clean:
	rm -rf $(OUTPUT_VALIDOS) $(OUTPUT_INVALIDOS)

help:
	@echo "Comandos disponíveis:"
	@echo "  make                - compila todos os válidos para $(OUTPUT_VALIDOS)/"
	@echo "  make invalidos      - executa todos os inválidos mostrando erros"
	@echo "  make test_valid ARQ=exemplo - compila input/validos/exemplo.homi -> output/validos/exemplo.yaml"
	@echo "  make test_invalid ARQ=exemplo - executa input/invalidos/exemplo.homi (esperado erro)"
	@echo "  make run ARQ=arquivo.homi      - executa um arquivo arbitrário"
	@echo "  make clean          - remove pastas output"