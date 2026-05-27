import argparse
import sys
from pathlib import Path

from compiler.generator import YamlGenerator
from compiler.lexer import Lexer
from compiler.parser import Parser
from compiler.semantics import SemanticAnalyzer


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compilador Homi: converte scripts Homi em YAML do Home Assistant"
    )
    parser.add_argument("input", help="Arquivo .homi de entrada")
    parser.add_argument("-o", "--output", default="automations.yaml", help="Arquivo YAML de saida")
    parser.add_argument("--force", action="store_true", help="Gera YAML mesmo com erros")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Arquivo nao encontrado: {input_path}", file=sys.stderr)
        return 1

    text = input_path.read_text(encoding="utf-8")

    lexer = Lexer(text)
    tokens = lexer.tokenize()

    parser_instance = Parser(tokens)
    program = parser_instance.parse()

    semantic = SemanticAnalyzer()
    context = semantic.analyze(program)

    errors = []
    errors.extend(lexer.errors)
    errors.extend(parser_instance.errors)
    errors.extend(context.errors)

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        if not args.force:
            return 1

    yaml_text = YamlGenerator(context.symbols).generate(program)
    output_path = Path(args.output)
    output_path.write_text(yaml_text, encoding="utf-8")
    print(f"YAML gerado: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
