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


class Parser:
    def __init__(self, tokens: List[Token]) -> None:
        self.tokens = tokens
        self.pos = 0
        self.errors: List[str] = []

    def parse(self) -> Program:
        entities: List[EntityDecl] = []
        automations: List[Automation] = []

        if self._check("entidades"):
            entities = self._parse_entities_block()

        while self._check("automacao"):
            automation = self._parse_automation()
            if automation:
                automations.append(automation)

        if not self._check("EOF"):
            self._error_at(self._current(), "tokens inesperados no fim do arquivo")
        return Program(entities=entities, automations=automations)

    def _parse_entities_block(self) -> List[EntityDecl]:
        decls: List[EntityDecl] = []
        self._expect("entidades", {"automacao", "EOF"})
        self._expect("LBRACE", {"RBRACE"})
        while self._check_any({
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
        }):
            decl = self._parse_declaration()
            if decl:
                decls.append(decl)
        self._expect("RBRACE", {"automacao", "EOF"})
        return decls

    def _parse_declaration(self) -> Optional[EntityDecl]:
        type_tok = self._advance()
        alias_tok = self._expect("IDENT", {"ASSIGN", "SEMICOLON", "RBRACE"})
        self._expect("ASSIGN", {"ENTITY_ID", "SEMICOLON"})
        entity_tok = self._expect("ENTITY_ID", {"SEMICOLON"})
        self._expect("SEMICOLON", {"RBRACE", "automacao", "entidades"})

        if not alias_tok or not entity_tok:
            return None
        return EntityDecl(
            type_name=type_tok.lexeme,
            alias=alias_tok.lexeme,
            entity_id=entity_tok.lexeme,
            line=type_tok.line,
        )

    def _parse_automation(self) -> Optional[Automation]:
        start_tok = self._expect("automacao", {"STRING"})
        name_tok = self._expect("STRING", {"LBRACE"})
        self._expect("LBRACE", {"quando", "RBRACE"})

        triggers = self._parse_quando()
        condition = None
        if self._check("se"):
            condition = self._parse_se()
        actions = self._parse_entao()
        mode = None
        if self._check("modo"):
            mode = self._parse_modo()
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
        triggers: List[Any] = []
        self._expect("quando", {"SEMICOLON"})
        trigger = self._parse_trigger()
        if trigger:
            triggers.append(trigger)
        while self._match("ou"):
            trigger = self._parse_trigger()
            if trigger:
                triggers.append(trigger)
        self._expect("SEMICOLON", {"se", "entao", "modo", "RBRACE"})
        return triggers

    def _parse_trigger(self) -> Optional[Any]:
        if self._check_any({"IDENT", "ENTITY_ID"}):
            return self._parse_state_trigger()
        if self._check("evento"):
            return self._parse_event_trigger()
        if self._check("hora"):
            return self._parse_time_trigger()
        if self._check("entre"):
            return self._parse_between_trigger()
        if self._check_any({"por_do_sol", "nascer_do_sol"}):
            return self._parse_sun_trigger()
        if self._check("dispositivo"):
            return self._parse_device_trigger()
        self._error_at(self._current(), "gatilho invalido")
        self._panic({"SEMICOLON", "se", "entao", "modo", "RBRACE"})
        return None

    def _parse_state_trigger(self) -> Optional[TriggerState]:
        ref = self._parse_entity_ref()
        self._expect("muda", {"para"})
        self._expect("para", {"SEMICOLON", "por"})
        state = self._parse_state_value()
        duration = None
        if self._match("por"):
            duration = self._parse_duration()
        if not ref:
            return None
        return TriggerState(entity=ref, to_state=state, duration=duration, line=ref.line)

    def _parse_event_trigger(self) -> Optional[TriggerEvent]:
        start = self._expect("evento", {"IDENT"})
        name_tok = self._expect("IDENT", {"SEMICOLON"})
        if not start or not name_tok:
            return None
        return TriggerEvent(event_name=name_tok.lexeme, line=start.line)

    def _parse_time_trigger(self) -> Optional[TriggerTime]:
        start = self._expect("hora", {"TIME"})
        time_tok = self._expect("TIME", {"SEMICOLON"})
        if not start or not time_tok:
            return None
        return TriggerTime(time=time_tok.lexeme, line=start.line)

    def _parse_between_trigger(self) -> Optional[TriggerBetween]:
        start = self._expect("entre", {"TIME"})
        start_time = self._expect("TIME", {"e"})
        self._expect("e", {"TIME"})
        end_time = self._expect("TIME", {"SEMICOLON"})
        if not start or not start_time or not end_time:
            return None
        return TriggerBetween(start=start_time.lexeme, end=end_time.lexeme, line=start.line)

    def _parse_sun_trigger(self) -> Optional[TriggerSun]:
        tok = self._advance()
        offset = None
        offset_sign = None
        if self._match("PLUS"):
            offset_sign = "+"
            offset = self._parse_duration()
        elif self._match("MINUS"):
            offset_sign = "-"
            offset = self._parse_duration()
        event = "sunset" if tok.type == "por_do_sol" else "sunrise"
        return TriggerSun(event=event, offset=offset, offset_sign=offset_sign, line=tok.line)

    def _parse_device_trigger(self) -> Optional[TriggerDevice]:
        start = self._expect("dispositivo", {"IDENT", "ENTITY_ID"})
        ref = self._parse_entity_ref()
        event_tok = self._expect_any({"IDENT", "STATE"}, {"por", "SEMICOLON"})
        duration = None
        if self._match("por"):
            duration = self._parse_duration()
        if not start or not ref or not event_tok:
            return None
        return TriggerDevice(entity=ref, event=event_tok.lexeme, duration=duration, line=start.line)

    def _parse_se(self) -> Optional[Any]:
        self._expect("se", {"SEMICOLON"})
        expr = self._parse_expr_or()
        self._expect("SEMICOLON", {"entao", "modo", "RBRACE"})
        return expr

    def _parse_entao(self) -> List[Any]:
        self._expect("entao", {"SEMICOLON", "modo", "RBRACE"})
        actions = self._parse_action_list({"modo", "RBRACE"}, require_trailing=True)
        return actions

    def _parse_modo(self) -> Optional[str]:
        self._expect("modo", {"IDENT", "single", "restart", "queued", "parallel"})
        tok = self._expect_any({"single", "restart", "queued", "parallel", "IDENT"}, {"SEMICOLON"})
        self._expect("SEMICOLON", {"RBRACE"})
        if not tok:
            return None
        return tok.lexeme

    def _parse_expr_or(self) -> Any:
        left = self._parse_expr_and()
        items = [left]
        while self._match("ou"):
            items.append(self._parse_expr_and())
        if len(items) == 1:
            return left
        return ExprOr(items=items, line=items[0].line)

    def _parse_expr_and(self) -> Any:
        left = self._parse_expr_not()
        items = [left]
        while self._match("e"):
            items.append(self._parse_expr_not())
        if len(items) == 1:
            return left
        return ExprAnd(items=items, line=items[0].line)

    def _parse_expr_not(self) -> Any:
        if self._match("nao"):
            item = self._parse_expr_not()
            return ExprNot(item=item, line=item.line)
        return self._parse_primary_cond()

    def _parse_primary_cond(self) -> Any:
        if self._match("LPAREN"):
            expr = self._parse_expr_or()
            self._expect("RPAREN", {"SEMICOLON", "entao", "senao"})
            return expr
        return self._parse_condition()

    def _parse_condition(self) -> Any:
        if self._check("hora"):
            return self._parse_time_condition()
        if self._check("sol"):
            return self._parse_sun_condition()
        if self._check("dispositivo"):
            return self._parse_device_condition()
        if self._check_any({"IDENT", "ENTITY_ID"}):
            return self._parse_state_condition()
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
        if self._match("entre"):
            after_tok = self._expect("TIME", {"e"})
            self._expect("e", {"TIME"})
            before_tok = self._expect("TIME", {"SEMICOLON", "entao", "senao", "RPAREN"})
            return ConditionAtom(
                kind="time",
                data={"after": after_tok.lexeme if after_tok else "", "before": before_tok.lexeme if before_tok else ""},
                line=start.line if start else self._current().line,
            )
        if self._match("depois"):
            time_tok = self._expect("TIME", {"SEMICOLON", "entao", "senao", "RPAREN"})
            return ConditionAtom(
                kind="time",
                data={"after": time_tok.lexeme if time_tok else ""},
                line=start.line if start else self._current().line,
            )
        if self._match("antes"):
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
        if self._match("ligar"):
            ref = self._parse_entity_ref()
            return ActionTurn(turn_on=True, entity=ref, line=ref.line)
        if self._match("desligar"):
            ref = self._parse_entity_ref()
            return ActionTurn(turn_on=False, entity=ref, line=ref.line)
        if self._match("esperar"):
            duration = self._parse_duration()
            return ActionDelay(duration=duration, line=duration.line)
        if self._match("notificar"):
            msg_tok = self._expect("STRING", {"SEMICOLON"})
            msg = msg_tok.lexeme if msg_tok else ""
            return ActionNotify(message=msg, line=msg_tok.line if msg_tok else self._current().line)
        if self._match("timer"):
            ref = self._parse_entity_ref()
            op_tok = self._expect_any({"iniciar", "parar", "finalizar"}, {"SEMICOLON"})
            op = op_tok.lexeme if op_tok else ""
            return ActionTimer(entity=ref, operation=op, line=ref.line)
        if self._match("servico"):
            domain_tok = self._expect("IDENT", {"DOT"})
            self._expect("DOT", {"IDENT"})
            service_tok = self._expect("IDENT", {"LPAREN"})
            self._expect("LPAREN", {"RPAREN"})
            args = self._parse_args()
            self._expect("RPAREN", {"SEMICOLON"})
            domain = domain_tok.lexeme if domain_tok else ""
            service = service_tok.lexeme if service_tok else ""
            return ActionService(domain=domain, service=service, args=args, line=domain_tok.line if domain_tok else self._current().line)
        if self._check("se"):
            return self._parse_action_if()
        if self._check("escolha"):
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
        while self._match("caso"):
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
        args: Dict[str, Value] = {}
        if self._check("RPAREN"):
            return args
        key_tok = self._expect("IDENT", {"ASSIGN", "RPAREN"})
        self._expect("ASSIGN", {"RPAREN"})
        val = self._parse_value()
        if key_tok:
            args[key_tok.lexeme] = val
        while self._match("COMMA"):
            key_tok = self._expect("IDENT", {"ASSIGN", "RPAREN"})
            self._expect("ASSIGN", {"RPAREN"})
            val = self._parse_value()
            if key_tok:
                args[key_tok.lexeme] = val
        return args

    def _parse_value(self) -> Value:
        tok = self._current()
        if self._match("STRING"):
            return Value(kind="string", value=tok.lexeme, line=tok.line)
        if self._match("NUMBER"):
            return Value(kind="number", value=self._parse_number(tok.lexeme), line=tok.line)
        if self._match("BOOLEAN"):
            return Value(kind="boolean", value=(tok.lexeme == "true"), line=tok.line)
        if self._match("DURATION"):
            duration = self._parse_duration_from_lexeme(tok.lexeme, tok.line)
            return Value(kind="duration", value=duration, line=tok.line)
        if self._match("TIME"):
            return Value(kind="time", value=tok.lexeme, line=tok.line)
        if self._match("ENTITY_ID"):
            return Value(kind="entity", value=EntityRef(name=tok.lexeme, is_entity_id=True, line=tok.line), line=tok.line)
        if self._match("IDENT"):
            return Value(kind="ident", value=tok.lexeme, line=tok.line)
        if self._match("LBRACKET"):
            values = []
            if not self._check("RBRACKET"):
                values.append(self._parse_value())
                while self._match("COMMA"):
                    values.append(self._parse_value())
            self._expect("RBRACKET", {"COMMA", "RPAREN", "SEMICOLON"})
            return Value(kind="list", value=values, line=tok.line)
        if self._match("LBRACE"):
            items: Dict[str, Value] = {}
            if not self._check("RBRACE"):
                key_tok = self._expect("IDENT", {"COLON", "RBRACE"})
                self._expect("COLON", {"RBRACE"})
                val = self._parse_value()
                if key_tok:
                    items[key_tok.lexeme] = val
                while self._match("COMMA"):
                    key_tok = self._expect("IDENT", {"COLON", "RBRACE"})
                    self._expect("COLON", {"RBRACE"})
                    val = self._parse_value()
                    if key_tok:
                        items[key_tok.lexeme] = val
            self._expect("RBRACE", {"COMMA", "RPAREN", "SEMICOLON"})
            return Value(kind="map", value=items, line=tok.line)

        self._error_at(tok, "valor invalido")
        return Value(kind="invalid", value=None, line=tok.line)

    def _parse_entity_ref(self) -> EntityRef:
        tok = self._expect_any({"IDENT", "ENTITY_ID"}, {"SEMICOLON", "RPAREN"})
        is_entity_id = tok.type == "ENTITY_ID" if tok else False
        name = tok.lexeme if tok else ""
        line = tok.line if tok else self._current().line
        return EntityRef(name=name, is_entity_id=is_entity_id, line=line)

    def _parse_state_value(self) -> Any:
        tok = self._current()
        if self._match("STATE"):
            return tok.lexeme
        if self._match("STRING"):
            return tok.lexeme
        if self._match("NUMBER"):
            return self._parse_number(tok.lexeme)
        if self._match("IDENT"):
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

    def _error_at(self, token: Token, message: str) -> None:
        self.errors.append(f"[Sintatico] Linha {token.line}, Coluna {token.col}: {message}")

    def _panic(self, sync: Set[str]) -> None:
        while not self._check("EOF") and not self._check_any(sync):
            self._advance()
