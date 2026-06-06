from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .ast import (
    ActionChoose,
    ActionDelay,
    ActionIf,
    ActionNotify,
    ActionService,
    ActionTimer,
    ActionTurn,
    Automation,
    ChooseCase,
    ConditionAtom,
    EntityDecl,
    EntityRef,
    ExprAnd,
    ExprNot,
    ExprOr,
    Program,
    TriggerBetween,
    TriggerDevice,
    TriggerEvent,
    TriggerState,
    TriggerSun,
    TriggerTime,
    Value,
)


TYPE_DOMAINS = {
    "luz": {"light"},
    "sensor": {"sensor", "binary_sensor"},
    "interruptor": {"switch"},
    "alarme": {"alarm_control_panel"},
    "timer": {"timer"},
    "clima": {"weather", "climate"},
    "midia": {"media_player"},
    "cortina": {"cover"},
    "cena": {"scene"},
    "grupo": {"group"},
}

DOMAIN_TYPES = {
    "light": "luz",
    "sensor": "sensor",
    "binary_sensor": "sensor",
    "switch": "interruptor",
    "alarm_control_panel": "alarme",
    "timer": "timer",
    "weather": "clima",
    "climate": "clima",
    "media_player": "midia",
    "cover": "cortina",
    "scene": "cena",
    "group": "grupo",
    "automation": "automacao",
}

ALLOWED_STATES = {
    "luz": {"on", "off", "ligado", "desligado"},
    "interruptor": {"on", "off", "ligado", "desligado"},
    "alarme": {"disarmed", "armed", "desarmado", "armado"},
    "timer": {"idle", "active"},
    "midia": {"off", "on", "playing", "standby"},
}

SERVICE_CATALOG = {
    "light": {"turn_on", "turn_off", "toggle"},
    "switch": {"turn_on", "turn_off", "toggle"},
    "timer": {"start", "finish", "cancel"},
    "media_player": {"play_media", "turn_off", "volume_set"},
    "automation": {"trigger"},
    "notify": {"notify"},
}


@dataclass
class SemanticContext:
    symbols: Dict[str, EntityDecl]
    errors: List[str]


class SemanticAnalyzer:
    def analyze(self, program: Program) -> SemanticContext:
        symbols: Dict[str, EntityDecl] = {}
        errors: List[str] = []

        for decl in program.entities:
            if decl.alias in symbols:
                errors.append(
                    f"[Semantico] Linha {decl.line}: alias '{decl.alias}' duplicado"
                )
                continue
            domain = self._domain_from_entity_id(decl.entity_id)
            if not domain:
                errors.append(
                    f"[Semantico] Linha {decl.line}: entity_id invalido '{decl.entity_id}'"
                )
            else:
                allowed = TYPE_DOMAINS.get(decl.type_name, set())
                if allowed and domain not in allowed:
                    errors.append(
                        f"[Semantico] Linha {decl.line}: tipo '{decl.type_name}' nao compativel com dominio '{domain}'"
                    )
            symbols[decl.alias] = decl

        for automation in program.automations:
            self._check_automation(automation, symbols, errors)

        return SemanticContext(symbols=symbols, errors=errors)

    def _check_automation(self, automation: Automation, symbols: Dict[str, EntityDecl], errors: List[str]) -> None:
        for trigger in automation.triggers:
            self._check_trigger(trigger, symbols, errors)
        if automation.condition:
            self._check_expr(automation.condition, symbols, errors)
        for action in automation.actions:
            self._check_action(action, symbols, errors)
        if automation.mode and automation.mode not in {"single", "restart", "queued", "parallel"}:
            errors.append(
                f"[Semantico] Linha {automation.line}: modo invalido '{automation.mode}'"
            )

    def _check_trigger(self, trigger: object, symbols: Dict[str, EntityDecl], errors: List[str]) -> None:
        if isinstance(trigger, TriggerState):
            entity_id, type_name = self._resolve_entity(trigger.entity, symbols, errors)
            self._check_comparison(trigger.operator, trigger.to_state, trigger.line, errors)
            self._check_state_value(type_name, trigger.to_state, trigger.line, errors)
        elif isinstance(trigger, TriggerDevice):
            self._resolve_entity(trigger.entity, symbols, errors)
        elif isinstance(trigger, (TriggerEvent, TriggerTime, TriggerBetween, TriggerSun)):
            return

    def _check_expr(self, expr: object, symbols: Dict[str, EntityDecl], errors: List[str]) -> None:
        if isinstance(expr, ConditionAtom):
            kind = expr.kind
            if kind in {"state", "device"}:
                entity = expr.data.get("entity")
                state = expr.data.get("state")
                operator = expr.data.get("operator", "esta")
                self._check_comparison(operator, state, expr.line, errors)
                if isinstance(entity, EntityRef):
                    _, type_name = self._resolve_entity(entity, symbols, errors)
                    self._check_state_value(type_name, state, expr.line, errors)
        elif isinstance(expr, ExprAnd) or isinstance(expr, ExprOr):
            for item in expr.items:
                self._check_expr(item, symbols, errors)
        elif isinstance(expr, ExprNot):
            self._check_expr(expr.item, symbols, errors)

    def _check_action(self, action: object, symbols: Dict[str, EntityDecl], errors: List[str]) -> None:
        if isinstance(action, ActionTurn):
            _, type_name = self._resolve_entity(action.entity, symbols, errors)
            if type_name not in {"luz", "interruptor", "midia", "cortina", "clima"}:
                errors.append(
                    f"[Semantico] Linha {action.line}: acao ligar/desligar invalida para tipo '{type_name}'"
                )
        elif isinstance(action, ActionDelay):
            return
        elif isinstance(action, ActionNotify):
            return
        elif isinstance(action, ActionTimer):
            _, type_name = self._resolve_entity(action.entity, symbols, errors)
            if type_name != "timer":
                errors.append(
                    f"[Semantico] Linha {action.line}: acao timer invalida para tipo '{type_name}'"
                )
        elif isinstance(action, ActionService):
            domain = action.domain
            service = action.service
            if domain not in SERVICE_CATALOG:
                errors.append(
                    f"[Semantico] Linha {action.line}: dominio de servico desconhecido '{domain}'"
                )
            else:
                if service not in SERVICE_CATALOG[domain]:
                    errors.append(
                        f"[Semantico] Linha {action.line}: servico '{service}' nao existe no dominio '{domain}'"
                    )
            entity_arg = action.args.get("entity_id")
            if entity_arg:
                ent_id = self._value_to_entity_id(entity_arg, symbols, errors)
                if ent_id:
                    ent_domain = self._domain_from_entity_id(ent_id)
                    if ent_domain and ent_domain != domain:
                        errors.append(
                            f"[Semantico] Linha {action.line}: entity_id '{ent_id}' nao compativel com dominio '{domain}'"
                        )
        elif isinstance(action, ActionIf):
            self._check_expr(action.condition, symbols, errors)
            for act in action.then_actions:
                self._check_action(act, symbols, errors)
            if action.else_actions:
                for act in action.else_actions:
                    self._check_action(act, symbols, errors)
        elif isinstance(action, ActionChoose):
            for case in action.cases:
                self._check_expr(case.condition, symbols, errors)
                for act in case.actions:
                    self._check_action(act, symbols, errors)
            if action.default_actions:
                for act in action.default_actions:
                    self._check_action(act, symbols, errors)

    def _resolve_entity(self, ref: EntityRef, symbols: Dict[str, EntityDecl], errors: List[str]) -> Tuple[str, str]:
        if ref.is_entity_id:
            domain = self._domain_from_entity_id(ref.name)
            type_name = DOMAIN_TYPES.get(domain, "desconhecido")
            return ref.name, type_name
        if ref.name not in symbols:
            errors.append(
                f"[Semantico] Linha {ref.line}: alias '{ref.name}' nao declarado"
            )
            return ref.name, "desconhecido"
        decl = symbols[ref.name]
        return decl.entity_id, decl.type_name

    def _value_to_entity_id(self, value: Value, symbols: Dict[str, EntityDecl], errors: List[str]) -> Optional[str]:
        if value.kind == "entity" and isinstance(value.value, EntityRef):
            return self._resolve_entity(value.value, symbols, errors)[0]
        if value.kind == "ident":
            fake_ref = EntityRef(name=value.value, is_entity_id=False, line=value.line)
            return self._resolve_entity(fake_ref, symbols, errors)[0]
        if value.kind == "string":
            return value.value
        return None

    def _check_state_value(self, type_name: str, state: object, line: int, errors: List[str]) -> None:
        if type_name == "desconhecido":
            return
        if isinstance(state, (int, float)):
            if type_name not in {"sensor"}:
                errors.append(
                    f"[Semantico] Linha {line}: valor numerico invalido para tipo '{type_name}'"
                )
            return
        if isinstance(state, str):
            allowed = ALLOWED_STATES.get(type_name)
            if allowed and state not in allowed:
                errors.append(
                    f"[Semantico] Linha {line}: estado '{state}' invalido para tipo '{type_name}'"
                )

    def _check_comparison(self, operator: str, value: object, line: int, errors: List[str]) -> None:
        if operator in {">", "<", ">=", "<="} and not isinstance(value, (int, float)):
            errors.append(
                f"[Semantico] Linha {line}: operador '{operator}' exige valor numerico"
            )

    def _domain_from_entity_id(self, entity_id: str) -> Optional[str]:
        if "." not in entity_id:
            return None
        return entity_id.split(".", 1)[0]
