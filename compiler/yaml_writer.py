# Converte uma estrutura Python para texto YAML simples.
def dump_yaml(data):
    lines = []
    _emit(data, 0, lines)
    return "\n".join(lines) + "\n"


# Escreve um valor respeitando o nivel de indentacao.
def _emit(value, indent, lines):
    if isinstance(value, dict):
        for key, item in value.items():
            if _is_scalar(item):
                lines.append(" " * indent + f"{key}: {_yaml_scalar(item)}")
            else:
                lines.append(" " * indent + f"{key}:")
                _emit(item, indent + 2, lines)
        return

    if isinstance(value, list):
        _emit_list(value, indent, lines)
        return

    lines.append(" " * indent + _yaml_scalar(value))


# Escreve listas no formato YAML.
def _emit_list(items, indent, lines):
    for item in items:
        if isinstance(item, dict):
            _emit_dict_item(item, indent, lines)
        elif isinstance(item, list):
            lines.append(" " * indent + "-")
            _emit(item, indent + 2, lines)
        else:
            lines.append(" " * indent + f"- {_yaml_scalar(item)}")


# Escreve um dicionario dentro de uma lista.
def _emit_dict_item(item, indent, lines):
    if not item:
        lines.append(" " * indent + "- {}")
        return

    first_key = next(iter(item))
    first_val = item[first_key]
    rest = {k: v for k, v in item.items() if k != first_key}

    if _is_scalar(first_val):
        lines.append(" " * indent + f"- {first_key}: {_yaml_scalar(first_val)}")
        if rest:
            _emit(rest, indent + 2, lines)
        return

    lines.append(" " * indent + f"- {first_key}:")
    _emit(first_val, indent + 4, lines)
    if rest:
        _emit(rest, indent + 2, lines)


# Diz se um valor pode ser escrito em uma linha.
def _is_scalar(value):
    return not isinstance(value, (dict, list))


# Formata um valor escalar para YAML.
def _yaml_scalar(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        escaped = value.replace("'", "''")
        return f"'{escaped}'"
    return f"'{str(value)}'"
