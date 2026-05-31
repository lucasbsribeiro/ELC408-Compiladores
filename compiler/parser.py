from typing import Any, Dict, List, Optional, Set

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
    Duration,
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
from .lexer import Token


EPSILON = "epsilon"

TYPE_TOKENS = {
    "luz",
    "sensor",
    "interruptor",
    "alarme",
    "timer",
    "clima",
    "midia",
    "cortina",
    "cena",
    "grupo",
}

MODE_TOKENS = {"single", "restart", "queued", "parallel"}

VALUE_START = {
    "STRING",
    "NUMBER",
    "BOOLEAN",
    "DURATION",
    "TIME",
    "ENTITY_ID",
    "IDENT",
    "LBRACKET",
    "LBRACE",
}


PREDICTIVE_TABLE: Dict[str, Dict[str, str]] = {
    "bloco_entidades_opt": {
        "entidades": "bloco_entidades",
        "automacao": EPSILON,
        "EOF": EPSILON,
    },
    "lista_declaracoes": {**{tok: "declaracao" for tok in TYPE_TOKENS}, "RBRACE": EPSILON},
    "lista_automacoes": {"automacao": "automacao", "EOF": EPSILON},
    "lista_gatilhos_tail": {"ou": "ou_gatilho", "SEMICOLON": EPSILON},
    "gatilho": {
        "IDENT": "gatilho_estado",
        "ENTITY_ID": "gatilho_estado",
        "evento": "gatilho_evento",
        "hora": "gatilho_tempo",
        "entre": "gatilho_tempo",
        "por_do_sol": "gatilho_sol",
        "nascer_do_sol": "gatilho_sol",
        "dispositivo": "gatilho_dispositivo",
    },
    "gatilho_tempo": {"hora": "gatilho_hora", "entre": "gatilho_entre"},
    "gatilho_sol": {"por_do_sol": "sunset", "nascer_do_sol": "sunrise"},
    "janela_opt": {
        "por": "janela_por",
        "SEMICOLON": EPSILON,
        "ou": EPSILON,
        "se": EPSILON,
        "entao": EPSILON,
        "modo": EPSILON,
        "RBRACE": EPSILON,
    },
    "offset_opt": {
        "PLUS": "offset_plus",
        "MINUS": "offset_minus",
        "SEMICOLON": EPSILON,
        "ou": EPSILON,
        "se": EPSILON,
        "entao": EPSILON,
        "modo": EPSILON,
        "RBRACE": EPSILON,
    },
    "bloco_se_opt": {"se": "bloco_se", "entao": EPSILON},
    "expr_or_tail": {
        "ou": "expr_or_tail",
        "SEMICOLON": EPSILON,
        "entao": EPSILON,
        "senao": EPSILON,
        "RPAREN": EPSILON,
    },
    "expr_and_tail": {
        "e": "expr_and_tail",
        "ou": EPSILON,
        "SEMICOLON": EPSILON,
        "entao": EPSILON,
        "senao": EPSILON,
        "RPAREN": EPSILON,
    },
    "expr_not": {
        "nao": "expr_not_nao",
        "LPAREN": "expr_not_prim",
        "hora": "expr_not_prim",
        "sol": "expr_not_prim",
        "dispositivo": "expr_not_prim",
        "IDENT": "expr_not_prim",
        "ENTITY_ID": "expr_not_prim",
    },
    "prim_cond": {
        "LPAREN": "prim_group",
        "hora": "prim_cond",
        "sol": "prim_cond",
        "dispositivo": "prim_cond",
        "IDENT": "prim_cond",
        "ENTITY_ID": "prim_cond",
    },
    "condicao": {
        "hora": "condicao_tempo",
        "sol": "condicao_sol",
        "dispositivo": "condicao_dispositivo",
        "IDENT": "condicao_estado",
        "ENTITY_ID": "condicao_estado",
    },
    "condicao_tempo_tail": {
        "entre": "tempo_entre",
        "depois": "tempo_depois",
        "antes": "tempo_antes",
    },
    "lista_acoes_tail": {
        "SEMICOLON": "acao_tail",
        "senao": EPSILON,
        "caso": EPSILON,
        "modo": EPSILON,
        "RBRACE": EPSILON,
    },
    "acao": {
        "ligar": "acao_ligar",
        "desligar": "acao_desligar",
        "esperar": "acao_esperar",
        "notificar": "acao_notificar",
        "timer": "acao_timer",
        "servico": "acao_servico",
        "se": "acao_se",
        "escolha": "acao_escolha",
    },
    "acao_timer_tipo": {
        "iniciar": "timer_iniciar",
        "parar": "timer_parar",
        "finalizar": "timer_finalizar",
    },
    "args_opt": {"IDENT": "args", "RPAREN": EPSILON},
    "args_tail": {"COMMA": "args_tail", "RPAREN": EPSILON},
    "lista_casos": {"caso": "caso", "senao": EPSILON, "RBRACE": EPSILON},
    "senao_opt": {"senao": "senao", "RBRACE": EPSILON},
    "bloco_modo_opt": {"modo": "bloco_modo", "RBRACE": EPSILON},
    "modo": {**{tok: "modo" for tok in MODE_TOKENS}, "IDENT": "modo"},
    "ref_entidade": {"IDENT": "ref_ident", "ENTITY_ID": "ref_entity_id"},
    "valor": {
        "STRING": "valor_string",
        "NUMBER": "valor_number",
        "BOOLEAN": "valor_boolean",
        "DURATION": "valor_duration",
        "TIME": "valor_time",
        "ENTITY_ID": "valor_entity",
        "IDENT": "valor_ident",
        "LBRACKET": "valor_list",
        "LBRACE": "valor_map",
    },
    "lista_valores_opt": {**{tok: "lista_valores" for tok in VALUE_START}, "RBRACKET": EPSILON},
    "lista_valores_tail": {"COMMA": "lista_valores_tail", "RBRACKET": EPSILON},
    "mapa_itens_opt": {"IDENT": "mapa_itens", "RBRACE": EPSILON},
    "mapa_itens_tail": {"COMMA": "mapa_itens_tail", "RBRACE": EPSILON},
    "valor_estado": {
        "STATE": "estado_state",
        "STRING": "estado_string",
        "NUMBER": "estado_number",
        "IDENT": "estado_ident",
    },
}

SYNC_SETS: Dict[str, Set[str]] = {
    "programa": {"EOF"},
    "bloco_entidades_opt": {"automacao", "EOF"},
    "lista_declaracoes": {"RBRACE"},
    "lista_automacoes": {"EOF"},
    "lista_gatilhos_tail": {"SEMICOLON", "se", "entao", "modo", "RBRACE"},
    "gatilho": {"SEMICOLON", "se", "entao", "modo", "RBRACE"},
    "bloco_se_opt": {"entao", "modo", "RBRACE"},
    "expr_or_tail": {"SEMICOLON", "entao", "senao", "RPAREN"},
    "expr_and_tail": {"ou", "SEMICOLON", "entao", "senao", "RPAREN"},
    "expr_not": {"SEMICOLON", "entao", "senao", "RPAREN"},
    "prim_cond": {"SEMICOLON", "entao", "senao", "RPAREN"},
    "condicao": {"SEMICOLON", "entao", "senao", "RPAREN"},
    "condicao_tempo_tail": {"SEMICOLON", "entao", "senao", "RPAREN"},
    "acao": {"SEMICOLON", "senao", "caso", "RBRACE"},
    "lista_acoes_tail": {"modo", "RBRACE", "senao", "caso"},
    "args_opt": {"RPAREN"},
    "args_tail": {"RPAREN"},
    "lista_casos": {"senao", "RBRACE"},
    "senao_opt": {"RBRACE"},
    "bloco_modo_opt": {"RBRACE"},
    "modo": {"SEMICOLON"},
    "valor": {"COMMA", "RPAREN", "SEMICOLON", "RBRACKET", "RBRACE"},
    "lista_valores_opt": {"RBRACKET"},
    "lista_valores_tail": {"RBRACKET"},
    "mapa_itens_opt": {"RBRACE"},
    "mapa_itens_tail": {"RBRACE"},
    "ref_entidade": {"SEMICOLON", "RPAREN"},
    "valor_estado": {"SEMICOLON", "entao", "senao", "RPAREN"},
}


class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.pos = 0
        self.errors: List[str] = []

    def parse(self) -> Program:
        program = self._parse_program()
        if not self._check("EOF"):
            self._error_at(self._current(), "tokens inesperados no fim do arquivo")
        return program

    def _parse_program(self) -> Program:
        entities = self._parse_bloco_entidades_opt()
        automations = self._parse_lista_automacoes()
        return Program(entities=entities, automations=automations)

    def _parse_bloco_entidades_opt(self) -> List[EntityDecl]:
        prod = self._predict("bloco_entidades_opt")
        if prod == "bloco_entidades":
            return self._parse_entities_block()
        return []

    def _parse_entities_block(self) -> List[EntityDecl]:
        self._expect("entidades", {"LBRACE"})
        self._expect("LBRACE", {"RBRACE"})
        decls = self._parse_lista_declaracoes()
        self._expect("RBRACE", {"automacao", "EOF"})
        return decls

    def _parse_lista_declaracoes(self) -> List[EntityDecl]:
        decls: List[EntityDecl] = []
        while True:
            prod = self._predict("lista_declaracoes")
            if prod == EPSILON or prod is None:
                break
            decl = self._parse_declaration()
            if decl:
                decls.append(decl)
        return decls

    def _parse_declaration(self) -> Optional[EntityDecl]:
        type_tok = self._expect_any(TYPE_TOKENS, {"IDENT", "ASSIGN", "ENTITY_ID", "SEMICOLON", "RBRACE"})
        alias_tok = self._expect("IDENT", {"ASSIGN", "SEMICOLON", "RBRACE"})
        self._expect("ASSIGN", {"ENTITY_ID", "SEMICOLON"})
        entity_tok = self._expect("ENTITY_ID", {"SEMICOLON"})
        self._expect("SEMICOLON", {"RBRACE", "automacao", "entidades"})

        if not type_tok or not alias_tok or not entity_tok:
            return None
        return EntityDecl(
            type_name=type_tok.lexeme,
            alias=alias_tok.lexeme,
            entity_id=entity_tok.lexeme,
            line=type_tok.line,
        )

    def _parse_lista_automacoes(self) -> List[Automation]:
        automations: List[Automation] = []
        while True:
            prod = self._predict("lista_automacoes")
            if prod == EPSILON or prod is None:
                break
            automation = self._parse_automation()
            if automation:
                automations.append(automation)
        return automations

    def _parse_automation(self) -> Optional[Automation]:
        start_tok = self._expect("automacao", {"STRING"})
        name_tok = self._expect("STRING", {"LBRACE"})
        self._expect("LBRACE", {"quando", "RBRACE"})

        triggers = self._parse_quando()
        condition = self._parse_bloco_se_opt()
        actions = self._parse_entao()
        mode = self._parse_bloco_modo_opt()
        self._expect("RBRACE", {"automacao", "EOF"})

        if not start_tok or not name_tok:
            return None
        return Automation(
            name=name_tok.lexeme,
            triggers=triggers,
            condition=condition,
            actions=actions,
            mode=mode,
            line=start_tok.line,
        )

    def _parse_quando(self) -> List[Any]:
        self._expect("quando", {"SEMICOLON"})
        triggers = self._parse_lista_gatilhos()
        self._expect("SEMICOLON", {"se", "entao", "modo", "RBRACE"})
        return triggers

    def _parse_lista_gatilhos(self) -> List[Any]:
        triggers: List[Any] = []
        trigger = self._parse_trigger()
        if trigger:
            triggers.append(trigger)
        while True:
            prod = self._predict("lista_gatilhos_tail")
            if prod == EPSILON or prod is None:
                break
            self._expect("ou", {"SEMICOLON"})
            trigger = self._parse_trigger()
            if trigger:
                triggers.append(trigger)
        return triggers

    def _parse_trigger(self) -> Optional[Any]:
        prod = self._predict("gatilho")
        if prod == "gatilho_estado":
            return self._parse_state_trigger()
        if prod == "gatilho_evento":
            return self._parse_event_trigger()
        if prod == "gatilho_tempo":
            return self._parse_time_trigger()
        if prod == "gatilho_sol":
            return self._parse_sun_trigger()
        if prod == "gatilho_dispositivo":
            return self._parse_device_trigger()
        return None

    def _parse_state_trigger(self) -> Optional[TriggerState]:
        ref = self._parse_entity_ref()
        self._expect("muda", {"para"})
        self._expect("para", {"SEMICOLON", "por"})
        state = self._parse_state_value()
        duration = self._parse_janela_opt()
        if not ref:
            return None
        return TriggerState(entity=ref, to_state=state, duration=duration, line=ref.line)

    def _parse_event_trigger(self) -> Optional[TriggerEvent]:
        start = self._expect("evento", {"IDENT"})
        name_tok = self._expect("IDENT", {"SEMICOLON"})
        if not start or not name_tok:
            return None
        return TriggerEvent(event_name=name_tok.lexeme, line=start.line)

    def _parse_time_trigger(self) -> Optional[Any]:
        prod = self._predict("gatilho_tempo")
        if prod == "gatilho_hora":
            start = self._expect("hora", {"TIME"})
            time_tok = self._expect("TIME", {"SEMICOLON"})
            if not start or not time_tok:
                return None
            return TriggerTime(time=time_tok.lexeme, line=start.line)
        if prod == "gatilho_entre":
            start = self._expect("entre", {"TIME"})
            start_time = self._expect("TIME", {"e"})
            self._expect("e", {"TIME"})
            end_time = self._expect("TIME", {"SEMICOLON"})
            if not start or not start_time or not end_time:
                return None
            return TriggerBetween(start=start_time.lexeme, end=end_time.lexeme, line=start.line)
        return None

    def _parse_sun_trigger(self) -> Optional[TriggerSun]:
        prod = self._predict("gatilho_sol")
        tok = self._expect_any({"por_do_sol", "nascer_do_sol"}, {"SEMICOLON", "por", "entao", "modo", "RBRACE"})
        if not tok:
            return None
        offset, offset_sign = self._parse_offset_opt()
        event = "sunset" if prod == "sunset" else "sunrise"
        return TriggerSun(event=event, offset=offset, offset_sign=offset_sign, line=tok.line)

    def _parse_device_trigger(self) -> Optional[TriggerDevice]:
        start = self._expect("dispositivo", {"IDENT", "ENTITY_ID"})
        ref = self._parse_entity_ref()
        event_tok = self._expect_any({"IDENT", "STATE"}, {"por", "SEMICOLON"})
        duration = self._parse_janela_opt()
        if not start or not ref or not event_tok:
            return None
        return TriggerDevice(entity=ref, event=event_tok.lexeme, duration=duration, line=start.line)

    def _parse_janela_opt(self) -> Optional[Duration]:
        prod = self._predict("janela_opt")
        if prod == "janela_por":
            self._expect("por", {"DURATION"})
            return self._parse_duration()
        return None

    def _parse_offset_opt(self) -> tuple[Optional[Duration], Optional[str]]:
        prod = self._predict("offset_opt")
        if prod == "offset_plus":
            self._expect("PLUS", {"DURATION"})
            return self._parse_duration(), "+"
        if prod == "offset_minus":
            self._expect("MINUS", {"DURATION"})
            return self._parse_duration(), "-"
        return None, None

    def _parse_bloco_se_opt(self) -> Optional[Any]:
        prod = self._predict("bloco_se_opt")
        if prod == "bloco_se":
            return self._parse_se()
        return None

    def _parse_se(self) -> Optional[Any]:
        self._expect("se", {"SEMICOLON"})
        expr = self._parse_expr_or()
        self._expect("SEMICOLON", {"entao", "modo", "RBRACE"})
        return expr

    def _parse_entao(self) -> List[Any]:
        self._expect("entao", {"SEMICOLON", "modo", "RBRACE"})
        actions = self._parse_action_list({"modo", "RBRACE"}, require_trailing=True)
        return actions

    def _parse_bloco_modo_opt(self) -> Optional[str]:
        prod = self._predict("bloco_modo_opt")
        if prod == "bloco_modo":
            return self._parse_modo()
        return None

    def _parse_modo(self) -> Optional[str]:
        self._expect("modo", {"IDENT", "single", "restart", "queued", "parallel"})
        prod = self._predict("modo")
        if prod is None:
            return None
        tok = self._expect_any(MODE_TOKENS | {"IDENT"}, {"SEMICOLON"})
        self._expect("SEMICOLON", {"RBRACE"})
        if not tok:
            return None
        return tok.lexeme

    def _parse_expr_or(self) -> Any:
        left = self._parse_expr_and()
        items = [left]
        while True:
            prod = self._predict("expr_or_tail")
            if prod == EPSILON or prod is None:
                break
            self._expect("ou", {"SEMICOLON", "entao", "senao", "RPAREN"})
            items.append(self._parse_expr_and())
        if len(items) == 1:
            return left
        return ExprOr(items=items, line=items[0].line)

    def _parse_expr_and(self) -> Any:
        left = self._parse_expr_not()
        items = [left]
        while True:
            prod = self._predict("expr_and_tail")
            if prod == EPSILON or prod is None:
                break
            self._expect("e", {"ou", "SEMICOLON", "entao", "senao", "RPAREN"})
            items.append(self._parse_expr_not())
        if len(items) == 1:
            return left
        return ExprAnd(items=items, line=items[0].line)

    def _parse_expr_not(self) -> Any:
        prod = self._predict("expr_not")
        if prod == "expr_not_nao":
            self._expect("nao", {"LPAREN", "hora", "sol", "dispositivo", "IDENT", "ENTITY_ID"})
            item = self._parse_expr_not()
            return ExprNot(item=item, line=item.line)
        if prod == "expr_not_prim":
            return self._parse_primary_cond()
        return ConditionAtom(kind="invalid", data={}, line=self._current().line)

    def _parse_primary_cond(self) -> Any:
        prod = self._predict("prim_cond")
        if prod == "prim_group":
            self._expect("LPAREN", {"RPAREN"})
            expr = self._parse_expr_or()
            self._expect("RPAREN", {"SEMICOLON", "entao", "senao"})
            return expr
        return self._parse_condition()

    def _parse_condition(self) -> Any:
        prod = self._predict("condicao")
        if prod == "condicao_estado":
            return self._parse_state_condition()
        if prod == "condicao_tempo":
            return self._parse_time_condition()
        if prod == "condicao_sol":
            return self._parse_sun_condition()
        if prod == "condicao_dispositivo":
            return self._parse_device_condition()
        self._error_at(self._current(), "condicao invalida")
        self._panic({"SEMICOLON", "entao", "senao", "RPAREN"})
        return ConditionAtom(kind="invalid", data={}, line=self._current().line)

    def _parse_state_condition(self) -> ConditionAtom:
        ref = self._parse_entity_ref()
        self._expect("esta", {"STATE", "STRING", "NUMBER", "IDENT"})
        state = self._parse_state_value()
        return ConditionAtom(kind="state", data={"entity": ref, "state": state}, line=ref.line)

    def _parse_time_condition(self) -> ConditionAtom:
        start = self._expect("hora", {"entre", "depois", "antes"})
        prod = self._predict("condicao_tempo_tail")
        if prod == "tempo_entre":
            self._expect("entre", {"TIME"})
            after_tok = self._expect("TIME", {"e"})
            self._expect("e", {"TIME"})
            before_tok = self._expect("TIME", {"SEMICOLON", "entao", "senao", "RPAREN"})
            return ConditionAtom(
                kind="time",
                data={
                    "after": after_tok.lexeme if after_tok else "",
                    "before": before_tok.lexeme if before_tok else "",
                },
                line=start.line if start else self._current().line,
            )
        if prod == "tempo_depois":
            self._expect("depois", {"TIME"})
            time_tok = self._expect("TIME", {"SEMICOLON", "entao", "senao", "RPAREN"})
            return ConditionAtom(
                kind="time",
                data={"after": time_tok.lexeme if time_tok else ""},
                line=start.line if start else self._current().line,
            )
        if prod == "tempo_antes":
            self._expect("antes", {"TIME"})
            time_tok = self._expect("TIME", {"SEMICOLON", "entao", "senao", "RPAREN"})
            return ConditionAtom(
                kind="time",
                data={"before": time_tok.lexeme if time_tok else ""},
                line=start.line if start else self._current().line,
            )
        self._error_at(self._current(), "condicao de tempo invalida")
        return ConditionAtom(kind="time", data={}, line=start.line if start else self._current().line)

    def _parse_sun_condition(self) -> ConditionAtom:
        start = self._expect("sol", {"entre"})
        self._expect("entre", {"por_do_sol"})
        self._expect("por_do_sol", {"e"})
        self._expect("e", {"nascer_do_sol"})
        self._expect("nascer_do_sol", {"SEMICOLON", "entao", "senao", "RPAREN"})
        return ConditionAtom(kind="sun", data={}, line=start.line if start else self._current().line)

    def _parse_device_condition(self) -> ConditionAtom:
        start = self._expect("dispositivo", {"IDENT", "ENTITY_ID"})
        ref = self._parse_entity_ref()
        self._expect("esta", {"STATE", "STRING", "NUMBER", "IDENT"})
        state = self._parse_state_value()
        return ConditionAtom(kind="device", data={"entity": ref, "state": state}, line=start.line if start else self._current().line)

    def _parse_action_list(self, stop_types: Set[str], require_trailing: bool) -> List[Any]:
        actions: List[Any] = []
        if self._check_any(stop_types):
            self._error_at(self._current(), "acao esperada")
            return actions

        actions.append(self._parse_action())
        saw_semicolon = False

        while self._match("SEMICOLON"):
            saw_semicolon = True
            if self._check_any(stop_types):
                break
            actions.append(self._parse_action())

        if require_trailing and not saw_semicolon:
            self._error_at(self._current(), "esperado ';' ao final do bloco de acoes")

        return actions

    def _parse_action(self) -> Any:
        prod = self._predict("acao")
        if prod == "acao_ligar":
            self._expect("ligar", {"IDENT", "ENTITY_ID"})
            ref = self._parse_entity_ref()
            return ActionTurn(turn_on=True, entity=ref, line=ref.line)
        if prod == "acao_desligar":
            self._expect("desligar", {"IDENT", "ENTITY_ID"})
            ref = self._parse_entity_ref()
            return ActionTurn(turn_on=False, entity=ref, line=ref.line)
        if prod == "acao_esperar":
            self._expect("esperar", {"DURATION"})
            duration = self._parse_duration()
            return ActionDelay(duration=duration, line=duration.line)
        if prod == "acao_notificar":
            self._expect("notificar", {"STRING"})
            msg_tok = self._expect("STRING", {"SEMICOLON"})
            msg = msg_tok.lexeme if msg_tok else ""
            return ActionNotify(message=msg, line=msg_tok.line if msg_tok else self._current().line)
        if prod == "acao_timer":
            self._expect("timer", {"IDENT", "ENTITY_ID"})
            ref = self._parse_entity_ref()
            op_tok = self._expect_any({"iniciar", "parar", "finalizar"}, {"SEMICOLON"})
            op = op_tok.lexeme if op_tok else ""
            return ActionTimer(entity=ref, operation=op, line=ref.line)
        if prod == "acao_servico":
            self._expect("servico", {"IDENT"})
            domain_tok = self._expect("IDENT", {"DOT"})
            self._expect("DOT", {"IDENT"})
            service_tok = self._expect("IDENT", {"LPAREN"})
            self._expect("LPAREN", {"RPAREN"})
            args = self._parse_args()
            self._expect("RPAREN", {"SEMICOLON"})
            domain = domain_tok.lexeme if domain_tok else ""
            service = service_tok.lexeme if service_tok else ""
            return ActionService(domain=domain, service=service, args=args, line=domain_tok.line if domain_tok else self._current().line)
        if prod == "acao_se":
            return self._parse_action_if()
        if prod == "acao_escolha":
            return self._parse_action_choose()

        self._error_at(self._current(), "acao invalida")
        self._panic({"SEMICOLON", "senao", "caso", "RBRACE"})
        return ActionNotify(message="", line=self._current().line)

    def _parse_action_if(self) -> ActionIf:
        start = self._expect("se", {"entao"})
        cond = self._parse_expr_or()
        self._expect("entao", {"SEMICOLON", "senao", "RBRACE"})
        then_actions = self._parse_action_list({"senao", "modo", "RBRACE"}, require_trailing=False)
        else_actions = None
        if self._match("senao"):
            else_actions = self._parse_action_list({"modo", "RBRACE"}, require_trailing=False)
        return ActionIf(condition=cond, then_actions=then_actions, else_actions=else_actions, line=start.line if start else self._current().line)

    def _parse_action_choose(self) -> ActionChoose:
        start = self._expect("escolha", {"LBRACE"})
        self._expect("LBRACE", {"caso", "senao", "RBRACE"})
        cases: List[ChooseCase] = []
        while True:
            prod = self._predict("lista_casos")
            if prod == EPSILON or prod is None:
                break
            self._expect("caso", {"SEMICOLON"})
            cond = self._parse_expr_or()
            self._expect("ARROW", {"SEMICOLON"})
            actions = self._parse_action_list({"caso", "senao", "RBRACE"}, require_trailing=True)
            cases.append(ChooseCase(condition=cond, actions=actions, line=self._current().line))
        default_actions = None
        if self._match("senao"):
            default_actions = self._parse_action_list({"RBRACE"}, require_trailing=True)
        self._expect("RBRACE", {"SEMICOLON", "RBRACE", "modo"})
        return ActionChoose(cases=cases, default_actions=default_actions, line=start.line if start else self._current().line)

    def _parse_args(self) -> Dict[str, Value]:
        prod = self._predict("args_opt")
        if prod == EPSILON or prod is None:
            return {}
        return self._parse_args_list()

    def _parse_args_list(self) -> Dict[str, Value]:
        args: Dict[str, Value] = {}
        key, val = self._parse_arg()
        if key:
            args[key] = val
        while True:
            prod = self._predict("args_tail")
            if prod == EPSILON or prod is None:
                break
            self._expect("COMMA", {"IDENT"})
            key, val = self._parse_arg()
            if key:
                args[key] = val
        return args

    def _parse_arg(self) -> tuple[str, Value]:
        key_tok = self._expect("IDENT", {"ASSIGN", "RPAREN"})
        self._expect("ASSIGN", {"RPAREN"})
        val = self._parse_value()
        return key_tok.lexeme if key_tok else "", val

    def _parse_value(self) -> Value:
        prod = self._predict("valor")
        tok = self._current()
        if prod == "valor_string":
            self._expect("STRING", {"COMMA", "RPAREN", "SEMICOLON"})
            return Value(kind="string", value=tok.lexeme, line=tok.line)
        if prod == "valor_number":
            self._expect("NUMBER", {"COMMA", "RPAREN", "SEMICOLON"})
            return Value(kind="number", value=self._parse_number(tok.lexeme), line=tok.line)
        if prod == "valor_boolean":
            self._expect("BOOLEAN", {"COMMA", "RPAREN", "SEMICOLON"})
            return Value(kind="boolean", value=(tok.lexeme == "true"), line=tok.line)
        if prod == "valor_duration":
            self._expect("DURATION", {"COMMA", "RPAREN", "SEMICOLON"})
            duration = self._parse_duration_from_lexeme(tok.lexeme, tok.line)
            return Value(kind="duration", value=duration, line=tok.line)
        if prod == "valor_time":
            self._expect("TIME", {"COMMA", "RPAREN", "SEMICOLON"})
            return Value(kind="time", value=tok.lexeme, line=tok.line)
        if prod == "valor_entity":
            self._expect("ENTITY_ID", {"COMMA", "RPAREN", "SEMICOLON"})
            return Value(kind="entity", value=EntityRef(name=tok.lexeme, is_entity_id=True, line=tok.line), line=tok.line)
        if prod == "valor_ident":
            self._expect("IDENT", {"COMMA", "RPAREN", "SEMICOLON"})
            return Value(kind="ident", value=tok.lexeme, line=tok.line)
        if prod == "valor_list":
            self._expect("LBRACKET", {"RBRACKET"})
            values = self._parse_lista_valores_opt()
            self._expect("RBRACKET", {"COMMA", "RPAREN", "SEMICOLON"})
            return Value(kind="list", value=values, line=tok.line)
        if prod == "valor_map":
            self._expect("LBRACE", {"RBRACE"})
            items = self._parse_mapa_itens_opt()
            self._expect("RBRACE", {"COMMA", "RPAREN", "SEMICOLON"})
            return Value(kind="map", value=items, line=tok.line)

        self._error_at(tok, "valor invalido")
        return Value(kind="invalid", value=None, line=tok.line)

    def _parse_lista_valores_opt(self) -> List[Value]:
        prod = self._predict("lista_valores_opt")
        if prod == EPSILON or prod is None:
            return []
        values = [self._parse_value()]
        while True:
            prod = self._predict("lista_valores_tail")
            if prod == EPSILON or prod is None:
                break
            self._expect("COMMA", {"COMMA", "RBRACKET"})
            values.append(self._parse_value())
        return values

    def _parse_mapa_itens_opt(self) -> Dict[str, Value]:
        prod = self._predict("mapa_itens_opt")
        if prod == EPSILON or prod is None:
            return {}
        items: Dict[str, Value] = {}
        key, val = self._parse_mapa_item()
        if key:
            items[key] = val
        while True:
            prod = self._predict("mapa_itens_tail")
            if prod == EPSILON or prod is None:
                break
            self._expect("COMMA", {"IDENT"})
            key, val = self._parse_mapa_item()
            if key:
                items[key] = val
        return items

    def _parse_mapa_item(self) -> tuple[str, Value]:
        key_tok = self._expect("IDENT", {"COLON", "RBRACE"})
        self._expect("COLON", {"RBRACE"})
        val = self._parse_value()
        return key_tok.lexeme if key_tok else "", val

    def _parse_entity_ref(self) -> EntityRef:
        prod = self._predict("ref_entidade")
        tok = self._expect_any({"IDENT", "ENTITY_ID"}, {"SEMICOLON", "RPAREN"})
        is_entity_id = tok.type == "ENTITY_ID" if tok else False
        name = tok.lexeme if tok else ""
        line = tok.line if tok else self._current().line
        return EntityRef(name=name, is_entity_id=is_entity_id, line=line)

    def _parse_state_value(self) -> Any:
        prod = self._predict("valor_estado")
        tok = self._current()
        if prod == "estado_state":
            self._expect("STATE", {"SEMICOLON", "entao", "senao", "RPAREN"})
            return tok.lexeme
        if prod == "estado_string":
            self._expect("STRING", {"SEMICOLON", "entao", "senao", "RPAREN"})
            return tok.lexeme
        if prod == "estado_number":
            self._expect("NUMBER", {"SEMICOLON", "entao", "senao", "RPAREN"})
            return self._parse_number(tok.lexeme)
        if prod == "estado_ident":
            self._expect("IDENT", {"SEMICOLON", "entao", "senao", "RPAREN"})
            return tok.lexeme
        self._error_at(tok, "estado invalido")
        return tok.lexeme

    def _parse_duration(self) -> Duration:
        tok = self._expect("DURATION", {"SEMICOLON", "RPAREN"})
        if not tok:
            return Duration(value=0, unit="s", line=self._current().line)
        return self._parse_duration_from_lexeme(tok.lexeme, tok.line)

    def _parse_duration_from_lexeme(self, lexeme: str, line: int) -> Duration:
        unit = "s"
        for candidate in ("ms", "min", "s", "h", "d"):
            if lexeme.endswith(candidate):
                unit = candidate
                num = lexeme[: -len(candidate)]
                return Duration(value=float(num), unit=unit, line=line)
        return Duration(value=float(lexeme), unit=unit, line=line)

    def _parse_number(self, lexeme: str) -> Any:
        if "." in lexeme:
            return float(lexeme)
        return int(lexeme)

    def _current(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        if not self._check("EOF"):
            self.pos += 1
        return self.tokens[self.pos - 1]

    def _match(self, token_type: str) -> bool:
        if self._check(token_type):
            self._advance()
            return True
        return False

    def _check(self, token_type: str) -> bool:
        return self._current().type == token_type

    def _check_any(self, token_types: Set[str]) -> bool:
        return self._current().type in token_types

    def _expect(self, token_type: str, sync: Set[str]) -> Optional[Token]:
        if self._check(token_type):
            return self._advance()
        self._error_at(self._current(), f"esperado '{token_type}'")
        self._panic(sync)
        return None

    def _expect_any(self, token_types: Set[str], sync: Set[str]) -> Optional[Token]:
        if self._check_any(token_types):
            return self._advance()
        names = ", ".join(sorted(token_types))
        self._error_at(self._current(), f"esperado um de: {names}")
        self._panic(sync)
        return None

    def _predict(self, nonterminal: str) -> Optional[str]:
        table = PREDICTIVE_TABLE.get(nonterminal, {})
        lookahead = self._current().type
        prod = table.get(lookahead)
        if prod is None:
            self._error_at(self._current(), f"esperado <{nonterminal}>")
            self._panic(SYNC_SETS.get(nonterminal, {"SEMICOLON", "RBRACE", "EOF"}))
            return None
        return prod

    def _error_at(self, token: Token, message: str) -> None:
        self.errors.append(f"[Sintatico] Linha {token.line}, Coluna {token.col}: {message}")

    def _panic(self, sync: Set[str]) -> None:
        while not self._check("EOF") and not self._check_any(sync):
            self._advance()