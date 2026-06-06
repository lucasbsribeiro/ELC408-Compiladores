# Guarda o programa completo.
class Program:
    # Inicializa o programa.
    def __init__(self, entities=None, automations=None):
        self.entities = entities or []
        self.automations = automations or []


# Guarda uma entidade declarada.
class EntityDecl:
    # Inicializa uma entidade declarada.
    def __init__(self, type_name, alias, entity_id, line):
        self.type_name = type_name
        self.alias = alias
        self.entity_id = entity_id
        self.line = line


# Guarda uma referencia para entidade ou alias.
class EntityRef:
    # Inicializa uma referencia de entidade.
    def __init__(self, name, is_entity_id, line):
        self.name = name
        self.is_entity_id = is_entity_id
        self.line = line


# Guarda uma duracao com unidade.
class Duration:
    # Inicializa uma duracao.
    def __init__(self, value, unit, line):
        self.value = value
        self.unit = unit
        self.line = line


# Guarda um valor de argumento.
class Value:
    # Inicializa um valor.
    def __init__(self, kind, value, line):
        self.kind = kind
        self.value = value
        self.line = line


# Guarda uma automacao.
class Automation:
    # Inicializa uma automacao.
    def __init__(self, name, triggers, condition, actions, mode, line):
        self.name = name
        self.triggers = triggers
        self.condition = condition
        self.actions = actions
        self.mode = mode
        self.line = line


# Guarda um gatilho por estado.
class TriggerState:
    # Inicializa um gatilho de estado.
    def __init__(self, entity, operator, to_state, duration, line):
        self.entity = entity
        self.operator = operator
        self.to_state = to_state
        self.duration = duration
        self.line = line
        self.kind = "state"


# Guarda um gatilho por evento.
class TriggerEvent:
    # Inicializa um gatilho de evento.
    def __init__(self, event_name, line):
        self.event_name = event_name
        self.line = line
        self.kind = "event"


# Guarda um gatilho por horario.
class TriggerTime:
    # Inicializa um gatilho de horario.
    def __init__(self, time, line):
        self.time = time
        self.line = line
        self.kind = "time"


# Guarda um gatilho por intervalo de horario.
class TriggerBetween:
    # Inicializa um gatilho de intervalo.
    def __init__(self, start, end, line):
        self.start = start
        self.end = end
        self.line = line
        self.kind = "between"


# Guarda um gatilho solar.
class TriggerSun:
    # Inicializa um gatilho solar.
    def __init__(self, event, offset, offset_sign, line):
        self.event = event
        self.offset = offset
        self.offset_sign = offset_sign
        self.line = line
        self.kind = "sun"


# Guarda um gatilho de dispositivo.
class TriggerDevice:
    # Inicializa um gatilho de dispositivo.
    def __init__(self, entity, event, duration, line):
        self.entity = entity
        self.event = event
        self.duration = duration
        self.line = line
        self.kind = "device"


# Guarda uma condicao simples.
class ConditionAtom:
    # Inicializa uma condicao simples.
    def __init__(self, kind, data, line):
        self.kind = kind
        self.data = data
        self.line = line


# Guarda uma expressao com e.
class ExprAnd:
    # Inicializa uma expressao e.
    def __init__(self, items, line):
        self.items = items
        self.line = line


# Guarda uma expressao com ou.
class ExprOr:
    # Inicializa uma expressao ou.
    def __init__(self, items, line):
        self.items = items
        self.line = line


# Guarda uma expressao negada.
class ExprNot:
    # Inicializa uma expressao negada.
    def __init__(self, item, line):
        self.item = item
        self.line = line


# Guarda uma acao de ligar ou desligar.
class ActionTurn:
    # Inicializa uma acao de ligar ou desligar.
    def __init__(self, turn_on, entity, line):
        self.turn_on = turn_on
        self.entity = entity
        self.line = line
        self.kind = "turn"


# Guarda uma acao de espera.
class ActionDelay:
    # Inicializa uma acao de espera.
    def __init__(self, duration, line):
        self.duration = duration
        self.line = line
        self.kind = "delay"


# Guarda uma acao de notificacao.
class ActionNotify:
    # Inicializa uma acao de notificacao.
    def __init__(self, message, line):
        self.message = message
        self.line = line
        self.kind = "notify"


# Guarda uma acao de timer.
class ActionTimer:
    # Inicializa uma acao de timer.
    def __init__(self, entity, operation, line):
        self.entity = entity
        self.operation = operation
        self.line = line
        self.kind = "timer"


# Guarda uma chamada de servico.
class ActionService:
    # Inicializa uma acao de servico.
    def __init__(self, domain, service, args, line):
        self.domain = domain
        self.service = service
        self.args = args
        self.line = line
        self.kind = "service"


# Guarda uma acao condicional.
class ActionIf:
    # Inicializa uma acao condicional.
    def __init__(self, condition, then_actions, else_actions, line):
        self.condition = condition
        self.then_actions = then_actions
        self.else_actions = else_actions
        self.line = line
        self.kind = "if"


# Guarda um caso de escolha.
class ChooseCase:
    # Inicializa um caso de escolha.
    def __init__(self, condition, actions, line):
        self.condition = condition
        self.actions = actions
        self.line = line


# Guarda uma acao escolha.
class ActionChoose:
    # Inicializa uma acao escolha.
    def __init__(self, cases, default_actions, line):
        self.cases = cases
        self.default_actions = default_actions
        self.line = line
        self.kind = "choose"
