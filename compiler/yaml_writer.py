from typing import Any, Dict, List


def dump_yaml(data: Any) -> str:
    lines: List[str] = []
    _emit(data, 0, lines)
    return "\n".join(lines) + "\n"


def _emit(value: Any, indent: int, lines: List[str]) -> None:
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


def _emit_list(items: List[Any], indent: int, lines: List[str]) -> None:
    for item in items:
        if isinstance(item, dict):
            if not item:
                lines.append(" " * indent + "- {}")
                continue
            first_key = next(iter(item))
            first_val = item[first_key]
            rest = {k: v for k, v in item.items() if k != first_key}
            if _is_scalar(first_val):
                lines.append(
                    " " * indent + f"- {first_key}: {_yaml_scalar(first_val)}"
                )
                if rest:
                    _emit(rest, indent + 2, lines)
            else:
                lines.append(" " * indent + f"- {first_key}:")
                _emit(first_val, indent + 4, lines)
                if rest:
                    _emit(rest, indent + 2, lines)
        elif isinstance(item, list):
            lines.append(" " * indent + "-")
            _emit(item, indent + 2, lines)
        else:
            lines.append(" " * indent + f"- {_yaml_scalar(item)}")


def _is_scalar(value: Any) -> bool:
    return not isinstance(value, (dict, list))


def _yaml_scalar(value: Any) -> str:
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
