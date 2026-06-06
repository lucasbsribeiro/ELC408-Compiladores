from .ast import (
    ActionChoose,
    ActionDelay,
    ActionIf,
    ActionNotify,
    ActionService,
    ActionTimer,
    ActionTurn,
    ConditionAtom,
    EntityRef,
    ExprAnd,
    ExprNot,
    ExprOr,
    TriggerBetween,
    TriggerDevice,
    TriggerEvent,
    TriggerState,
    TriggerSun,
    TriggerTime,
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


class SemanticContext:
    # Guarda simbolos e erros da analise semantica.
    def __init__(self, symbols, errors):
        self.symbols = symbols
        self.errors = errors


class SemanticAnalyzer:
    # Analisa o programa e retorna contexto semantico.
    def analyze(self, program):
        symbols = {}
        errors = []

        for decl in program.entities:
            self._check_declaration(decl, symbols, errors)
        for automation in program.automations:
            self._check_automation(automation, symbols, errors)

        return SemanticContext(symbols, errors)

    # Valida uma declaracao de entidade.
    def _check_declaration(self, decl, symbols, errors):
        if decl.alias in symbols:
            errors.append(f"[Semantico] Linha {decl.line}: alias '{decl.alias}' duplicado")
            return

        domain = self._domain_from_entity_id(decl.entity_id)
        if not domain:
            errors.append(f"[Semantico] Linha {decl.line}: entity_id invalido '{decl.entity_id}'")
        elif domain not in TYPE_DOMAINS.get(decl.type_name, set()):
            errors.append(
                f"[Semantico] Linha {decl.line}: tipo '{decl.type_name}' nao compativel com dominio '{domain}'"
            )
        symbols[decl.alias] = decl

    # Valida uma automacao.
    def _check_automation(self, automation, symbols, errors):
        for trigger in automation.triggers:
            self._check_trigger(trigger, symbols, errors)
        if automation.condition:
            self._check_expr(automation.condition, symbols, errors)
        for action in automation.actions:
            self._check_action(action, symbols, errors)
        if automation.mode and automation.mode not in {"single", "restart", "queued", "parallel"}:
            errors.append(f"[Semantico] Linha {automation.line}: modo invalido '{automation.mode}'")

    # Valida um gatilho.
    def _check_trigger(self, trigger, symbols, errors):
        if isinstance(trigger, TriggerState):
            _, type_name = self._resolve_entity(trigger.entity, symbols, errors)
            self._check_comparison(trigger.operator, trigger.to_state, trigger.line, errors)
            self._check_state_value(type_name, trigger.to_state, trigger.line, errors)
        elif isinstance(trigger, TriggerDevice):
            self._resolve_entity(trigger.entity, symbols, errors)
        elif isinstance(trigger, (TriggerEvent, TriggerTime, TriggerBetween, TriggerSun)):
            return

    # Valida uma expressao condicional.
    def _check_expr(self, expr, symbols, errors):
        if isinstance(expr, ConditionAtom):
            self._check_atom(expr, symbols, errors)
        elif isinstance(expr, (ExprAnd, ExprOr)):
            for item in expr.items:
                self._check_expr(item, symbols, errors)
        elif isinstance(expr, ExprNot):
            self._check_expr(expr.item, symbols, errors)

    # Valida uma condicao simples.
    def _check_atom(self, atom, symbols, errors):
        if atom.kind not in {"state", "device"}:
            return

        entity = atom.data.get("entity")
        state = atom.data.get("state")
        operator = atom.data.get("operator", "esta")
        self._check_comparison(operator, state, atom.line, errors)

        if isinstance(entity, EntityRef):
            _, type_name = self._resolve_entity(entity, symbols, errors)
            self._check_state_value(type_name, state, atom.line, errors)

    # Valida uma acao.
    def _check_action(self, action, symbols, errors):
        if isinstance(action, ActionTurn):
            self._check_turn_action(action, symbols, errors)
        elif isinstance(action, (ActionDelay, ActionNotify)):
            return
        elif isinstance(action, ActionTimer):
            self._check_timer_action(action, symbols, errors)
        elif isinstance(action, ActionService):
            self._check_service_action(action, symbols, errors)
        elif isinstance(action, ActionIf):
            self._check_if_action(action, symbols, errors)
        elif isinstance(action, ActionChoose):
            self._check_choose_action(action, symbols, errors)

    # Valida acao ligar ou desligar.
    def _check_turn_action(self, action, symbols, errors):
        _, type_name = self._resolve_entity(action.entity, symbols, errors)
        if type_name not in {"luz", "interruptor", "midia", "cortina", "clima"}:
            errors.append(
                f"[Semantico] Linha {action.line}: acao ligar/desligar invalida para tipo '{type_name}'"
            )

    # Valida acao timer.
    def _check_timer_action(self, action, symbols, errors):
        _, type_name = self._resolve_entity(action.entity, symbols, errors)
        if type_name != "timer":
            errors.append(f"[Semantico] Linha {action.line}: acao timer invalida para tipo '{type_name}'")

    # Valida chamada de servico.
    def _check_service_action(self, action, symbols, errors):
        if action.domain not in SERVICE_CATALOG:
            errors.append(f"[Semantico] Linha {action.line}: dominio de servico desconhecido '{action.domain}'")
        elif action.service not in SERVICE_CATALOG[action.domain]:
            errors.append(
                f"[Semantico] Linha {action.line}: servico '{action.service}' nao existe no dominio '{action.domain}'"
            )

        entity_arg = action.args.get("entity_id")
        if entity_arg:
            self._check_service_entity(action, entity_arg, symbols, errors)

    # Valida entity_id passado para servico.
    def _check_service_entity(self, action, entity_arg, symbols, errors):
        ent_id = self._value_to_entity_id(entity_arg, symbols, errors)
        ent_domain = self._domain_from_entity_id(ent_id) if ent_id else None
        if ent_domain and ent_domain != action.domain:
            errors.append(
                f"[Semantico] Linha {action.line}: entity_id '{ent_id}' nao compativel com dominio '{action.domain}'"
            )

    # Valida acao se.
    def _check_if_action(self, action, symbols, errors):
        self._check_expr(action.condition, symbols, errors)
        for item in action.then_actions:
            self._check_action(item, symbols, errors)
        if action.else_actions:
            for item in action.else_actions:
                self._check_action(item, symbols, errors)

    # Valida acao escolha.
    def _check_choose_action(self, action, symbols, errors):
        for case in action.cases:
            self._check_expr(case.condition, symbols, errors)
            for item in case.actions:
                self._check_action(item, symbols, errors)
        if action.default_actions:
            for item in action.default_actions:
                self._check_action(item, symbols, errors)

    # Resolve alias ou entity_id.
    def _resolve_entity(self, ref, symbols, errors):
        if ref.is_entity_id:
            domain = self._domain_from_entity_id(ref.name)
            return ref.name, DOMAIN_TYPES.get(domain, "desconhecido")
        if ref.name not in symbols:
            errors.append(f"[Semantico] Linha {ref.line}: alias '{ref.name}' nao declarado")
            return ref.name, "desconhecido"
        decl = symbols[ref.name]
        return decl.entity_id, decl.type_name

    # Extrai entity_id de um valor.
    def _value_to_entity_id(self, value, symbols, errors):
        if value.kind == "entity" and isinstance(value.value, EntityRef):
            return self._resolve_entity(value.value, symbols, errors)[0]
        if value.kind == "ident":
            ref = EntityRef(value.value, False, value.line)
            return self._resolve_entity(ref, symbols, errors)[0]
        if value.kind == "string":
            return value.value
        return None

    # Valida valor de estado.
    def _check_state_value(self, type_name, state, line, errors):
        if type_name == "desconhecido":
            return
        if isinstance(state, (int, float)):
            if type_name != "sensor":
                errors.append(f"[Semantico] Linha {line}: valor numerico invalido para tipo '{type_name}'")
            return

        allowed = ALLOWED_STATES.get(type_name)
        if isinstance(state, str) and allowed and state not in allowed:
            errors.append(f"[Semantico] Linha {line}: estado '{state}' invalido para tipo '{type_name}'")

    # Valida operador de comparacao.
    def _check_comparison(self, operator, value, line, errors):
        if operator in {">", "<", ">=", "<="} and not isinstance(value, (int, float)):
            errors.append(f"[Semantico] Linha {line}: operador '{operator}' exige valor numerico")

    # Extrai dominio de um entity_id.
    def _domain_from_entity_id(self, entity_id):
        if "." not in entity_id:
            return None
        return entity_id.split(".", 1)[0]
