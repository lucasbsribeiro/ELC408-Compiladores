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


TYPE_TOKENS = {
    "luz", "sensor", "interruptor", "alarme", "timer",
    "clima", "midia", "cortina", "cena", "grupo",
}

MODE_TOKENS = {"single", "restart", "queued", "parallel"}
COMPARISON_TOKENS = {"OP_EQ", "OP_NE", "OP_GT", "OP_LT", "OP_GE", "OP_LE", "esta"}
DEVICE_EVENT_TOKENS = {"pressionado", "girado", "movido"}
ACTION_START_TOKENS = {"ligar", "desligar", "esperar", "notificar", "timer", "servico", "se", "escolha"}
VALUE_START_TOKENS = {"STRING", "NUMBER", "BOOLEAN", "DURATION", "TIME", "ENTITY_ID", "IDENT", "LBRACKET", "LBRACE"}


class Parser:
    # Prepara o parser com a lista de tokens.
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.errors = []

    # Analisa o programa completo.
    def parse(self):
        program = self._parse_program()
        if not self._check("EOF"):
            self._error_at(self._current(), "tokens inesperados no fim do arquivo")
        return program

    # Analisa entidades opcionais e automacoes.
    def _parse_program(self):
        return Program(
            entities=self._parse_entities_block() if self._check("entidades") else [],
            automations=self._parse_automations(),
        )

    # Analisa o bloco entidades.
    def _parse_entities_block(self):
        self._expect("entidades", {"LBRACE"})
        self._expect("LBRACE", {"RBRACE"})
        decls = []
        while self._check_any(TYPE_TOKENS):
            decl = self._parse_declaration()
            if decl:
                decls.append(decl)
        self._expect("RBRACE", {"automacao", "EOF"})
        return decls

    # Analisa uma declaracao de entidade.
    def _parse_declaration(self):
        type_tok = self._expect_any(TYPE_TOKENS, {"IDENT", "ASSIGN", "ENTITY_ID", "SEMICOLON", "RBRACE"})
        alias_tok = self._expect("IDENT", {"ASSIGN", "SEMICOLON", "RBRACE"})
        self._expect("ASSIGN", {"ENTITY_ID", "SEMICOLON"})
        entity_tok = self._expect("ENTITY_ID", {"SEMICOLON"})
        self._expect("SEMICOLON", {"RBRACE", "automacao", "entidades"})

        if not type_tok or not alias_tok or not entity_tok:
            return None
        return EntityDecl(type_tok.lexeme, alias_tok.lexeme, entity_tok.lexeme, type_tok.line)

    # Analisa todas as automacoes.
    def _parse_automations(self):
        automations = []
        while self._check("automacao"):
            automation = self._parse_automation()
            if automation:
                automations.append(automation)
        return automations

    # Analisa uma automacao.
    def _parse_automation(self):
        start_tok = self._expect("automacao", {"STRING"})
        name_tok = self._expect("STRING", {"LBRACE"})
        self._expect("LBRACE", {"quando", "RBRACE"})

        triggers = self._parse_quando()
        condition = self._parse_optional_se()
        actions = self._parse_entao()
        mode = self._parse_optional_modo()
        self._expect("RBRACE", {"automacao", "EOF"})

        if not start_tok or not name_tok:
            return None
        return Automation(name_tok.lexeme, triggers, condition, actions, mode, start_tok.line)

    # Analisa o bloco quando.
    def _parse_quando(self):
        self._expect("quando", {"SEMICOLON"})
        triggers = [self._parse_trigger()]
        while self._match("ou"):
            triggers.append(self._parse_trigger())
        self._expect("SEMICOLON", {"se", "entao", "modo", "RBRACE"})
        return [trigger for trigger in triggers if trigger]

    # Analisa um gatilho.
    def _parse_trigger(self):
        if self._check_any({"IDENT", "ENTITY_ID"}):
            return self._parse_state_trigger()
        if self._check("evento"):
            return self._parse_event_trigger()
        if self._check_any({"hora", "entre"}):
            return self._parse_time_trigger()
        if self._check_any({"por_do_sol", "nascer_do_sol"}):
            return self._parse_sun_trigger()
        if self._check("dispositivo"):
            return self._parse_device_trigger()

        self._error_at(self._current(), "gatilho invalido")
        self._panic({"SEMICOLON", "se", "entao", "modo", "RBRACE"})
        return None

    # Analisa um gatilho de estado.
    def _parse_state_trigger(self):
        ref = self._parse_entity_ref()
        operator = self._parse_comparison_operator()
        state = self._parse_state_value()
        duration = self._parse_optional_duration_window()
        return TriggerState(ref, operator, state, duration, ref.line)

    # Analisa um gatilho de evento.
    def _parse_event_trigger(self):
        start = self._expect("evento", {"IDENT"})
        name_tok = self._expect("IDENT", {"SEMICOLON"})
        if not start or not name_tok:
            return None
        return TriggerEvent(name_tok.lexeme, start.line)

    # Analisa um gatilho de horario.
    def _parse_time_trigger(self):
        if self._match("hora"):
            time_tok = self._expect("TIME", {"SEMICOLON"})
            if not time_tok:
                return None
            return TriggerTime(time_tok.lexeme, time_tok.line)

        start = self._expect("entre", {"TIME"})
        start_time = self._expect("TIME", {"e"})
        self._expect("e", {"TIME"})
        end_time = self._expect("TIME", {"SEMICOLON"})
        if not start or not start_time or not end_time:
            return None
        return TriggerBetween(start_time.lexeme, end_time.lexeme, start.line)

    # Analisa um gatilho solar.
    def _parse_sun_trigger(self):
        tok = self._expect_any({"por_do_sol", "nascer_do_sol"}, {"SEMICOLON", "por", "entao", "modo", "RBRACE"})
        if not tok:
            return None
        offset, sign = self._parse_optional_offset()
        event = "sunset" if tok.type == "por_do_sol" else "sunrise"
        return TriggerSun(event, offset, sign, tok.line)

    # Analisa um gatilho de dispositivo.
    def _parse_device_trigger(self):
        start = self._expect("dispositivo", {"IDENT", "ENTITY_ID"})
        ref = self._parse_entity_ref()
        event_tok = self._expect_any(DEVICE_EVENT_TOKENS, {"por", "SEMICOLON"})
        duration = self._parse_optional_duration_window()
        if not start or not event_tok:
            return None
        return TriggerDevice(ref, event_tok.lexeme, duration, start.line)

    # Analisa uma janela opcional com por.
    def _parse_optional_duration_window(self):
        if self._match("por"):
            return self._parse_duration()
        return None

    # Analisa um offset solar opcional.
    def _parse_optional_offset(self):
        if self._match("PLUS"):
            return self._parse_duration(), "+"
        if self._match("MINUS"):
            return self._parse_duration(), "-"
        return None, None

    # Analisa o bloco se opcional da automacao.
    def _parse_optional_se(self):
        if not self._check("se"):
            return None
        self._expect("se", {"SEMICOLON"})
        expr = self._parse_expr_or()
        self._expect("SEMICOLON", {"entao", "modo", "RBRACE"})
        return expr

    # Analisa o bloco entao.
    def _parse_entao(self):
        self._expect("entao", {"LBRACE"})
        return self._parse_action_block({"modo", "RBRACE"})

    # Analisa o bloco modo opcional.
    def _parse_optional_modo(self):
        if not self._match("modo"):
            return None
        tok = self._expect_any(MODE_TOKENS | {"IDENT"}, {"SEMICOLON"})
        self._expect("SEMICOLON", {"RBRACE"})
        return tok.lexeme if tok else None

    # Analisa expressoes ligadas por ou.
    def _parse_expr_or(self):
        items = [self._parse_expr_and()]
        while self._match("ou"):
            items.append(self._parse_expr_and())
        return items[0] if len(items) == 1 else ExprOr(items, items[0].line)

    # Analisa expressoes ligadas por e.
    def _parse_expr_and(self):
        items = [self._parse_expr_not()]
        while self._match("e"):
            items.append(self._parse_expr_not())
        return items[0] if len(items) == 1 else ExprAnd(items, items[0].line)

    # Analisa negacao de expressao.
    def _parse_expr_not(self):
        if self._match("nao"):
            item = self._parse_expr_not()
            return ExprNot(item, item.line)
        return self._parse_primary_condition()

    # Analisa condicao agrupada ou simples.
    def _parse_primary_condition(self):
        if self._match("LPAREN"):
            expr = self._parse_expr_or()
            self._expect("RPAREN", {"SEMICOLON", "entao", "senao"})
            return expr
        return self._parse_condition()

    # Analisa uma condicao simples.
    def _parse_condition(self):
        if self._check_any({"IDENT", "ENTITY_ID"}):
            return self._parse_state_condition()
        if self._check("hora"):
            return self._parse_time_condition()
        if self._check("sol"):
            return self._parse_sun_condition()
        if self._check("dispositivo"):
            return self._parse_device_condition()

        self._error_at(self._current(), "condicao invalida")
        self._panic({"ARROW", "SEMICOLON", "entao", "senao", "RPAREN"})
        return ConditionAtom("invalid", {}, self._current().line)

    # Analisa condicao de estado.
    def _parse_state_condition(self):
        ref = self._parse_entity_ref()
        operator = self._parse_comparison_operator()
        state = self._parse_state_value()
        return ConditionAtom("state", {"entity": ref, "operator": operator, "state": state}, ref.line)

    # Analisa condicao de tempo.
    def _parse_time_condition(self):
        start = self._expect("hora", {"entre", "depois", "antes"})
        line = start.line if start else self._current().line

        if self._match("entre"):
            after = self._expect("TIME", {"e"})
            self._expect("e", {"TIME"})
            before = self._expect("TIME", {"ARROW", "SEMICOLON", "entao", "senao", "RPAREN"})
            return ConditionAtom("time", {
                "after": after.lexeme if after else "",
                "before": before.lexeme if before else "",
            }, line)
        if self._match("depois"):
            time_tok = self._expect("TIME", {"ARROW", "SEMICOLON", "entao", "senao", "RPAREN"})
            return ConditionAtom("time", {"after": time_tok.lexeme if time_tok else ""}, line)
        if self._match("antes"):
            time_tok = self._expect("TIME", {"ARROW", "SEMICOLON", "entao", "senao", "RPAREN"})
            return ConditionAtom("time", {"before": time_tok.lexeme if time_tok else ""}, line)

        self._error_at(self._current(), "condicao de tempo invalida")
        return ConditionAtom("time", {}, line)

    # Analisa condicao solar.
    def _parse_sun_condition(self):
        start = self._expect("sol", {"entre"})
        self._expect("entre", {"por_do_sol"})
        self._expect("por_do_sol", {"e"})
        self._expect("e", {"nascer_do_sol"})
        self._expect("nascer_do_sol", {"ARROW", "SEMICOLON", "entao", "senao", "RPAREN"})
        return ConditionAtom("sun", {}, start.line if start else self._current().line)

    # Analisa condicao de dispositivo.
    def _parse_device_condition(self):
        start = self._expect("dispositivo", {"IDENT", "ENTITY_ID"})
        ref = self._parse_entity_ref()
        self._expect("esta", {"STATE", "STRING", "NUMBER", "IDENT"})
        state = self._parse_state_value()
        return ConditionAtom("device", {"entity": ref, "state": state}, start.line if start else self._current().line)

    # Analisa operador de comparacao.
    def _parse_comparison_operator(self):
        tok = self._expect_any(COMPARISON_TOKENS, {"STATE", "STRING", "NUMBER", "IDENT"})
        return tok.lexeme if tok else "esta"

    # Analisa um bloco de acoes.
    def _parse_action_block(self, outer_sync):
        self._expect("LBRACE", {"RBRACE"} | outer_sync)
        actions = self._parse_action_list({"RBRACE"}, True, True)
        self._expect("RBRACE", outer_sync)
        return actions

    # Analisa uma lista de acoes.
    def _parse_action_list(self, stop_types, require_trailing, allow_empty=False):
        actions = []
        if self._check_any(stop_types):
            if not allow_empty:
                self._error_at(self._current(), "acao esperada")
            return actions

        while not self._check("EOF") and not self._check_any(stop_types):
            action = self._parse_action()
            actions.append(action)

            if self._match("SEMICOLON"):
                continue
            if self._check_any(stop_types):
                if require_trailing and self._action_requires_semicolon(action):
                    self._error_at(self._current(), "esperado ';' ao final do bloco de acoes")
                break
            if self._action_requires_semicolon(action):
                self._error_at(self._current(), "esperado ';' ao final da acao")
            if not self._check_any(ACTION_START_TOKENS):
                break

        return actions

    # Diz se a acao exige ponto e virgula.
    def _action_requires_semicolon(self, action):
        return not isinstance(action, (ActionIf, ActionChoose))

    # Analisa uma acao.
    def _parse_action(self):
        if self._match("ligar"):
            ref = self._parse_entity_ref()
            return ActionTurn(True, ref, ref.line)
        if self._match("desligar"):
            ref = self._parse_entity_ref()
            return ActionTurn(False, ref, ref.line)
        if self._match("esperar"):
            duration = self._parse_duration()
            return ActionDelay(duration, duration.line)
        if self._match("notificar"):
            msg = self._expect("STRING", {"SEMICOLON"})
            return ActionNotify(msg.lexeme if msg else "", msg.line if msg else self._current().line)
        if self._match("timer"):
            ref = self._parse_entity_ref()
            op = self._expect_any({"iniciar", "parar", "finalizar"}, {"SEMICOLON"})
            return ActionTimer(ref, op.lexeme if op else "", ref.line)
        if self._check("servico"):
            return self._parse_service_action()
        if self._check("se"):
            return self._parse_if_action()
        if self._check("escolha"):
            return self._parse_choose_action()

        self._error_at(self._current(), "acao invalida")
        self._panic({"SEMICOLON", "senao", "caso", "RBRACE"})
        return ActionNotify("", self._current().line)

    # Analisa uma acao servico.
    def _parse_service_action(self):
        start = self._expect("servico", {"IDENT"})
        domain = self._expect("IDENT", {"DOT"})
        self._expect("DOT", {"IDENT"})
        service = self._expect("IDENT", {"LPAREN"})
        self._expect("LPAREN", {"RPAREN"})
        args = self._parse_args()
        self._expect("RPAREN", {"SEMICOLON"})
        return ActionService(
            domain.lexeme if domain else "",
            service.lexeme if service else "",
            args,
            domain.line if domain else (start.line if start else self._current().line),
        )

    # Analisa uma acao se.
    def _parse_if_action(self):
        start = self._expect("se", {"LPAREN", "hora", "sol", "dispositivo", "IDENT", "ENTITY_ID", "nao"})
        condition = self._parse_expr_or()
        self._expect("entao", {"LBRACE"})
        then_actions = self._parse_action_block({"senao", "SEMICOLON", "RBRACE"})
        else_actions = self._parse_action_block({"SEMICOLON", "RBRACE"}) if self._match("senao") else None
        return ActionIf(condition, then_actions, else_actions, start.line if start else self._current().line)

    # Analisa uma acao escolha.
    def _parse_choose_action(self):
        start = self._expect("escolha", {"LBRACE"})
        self._expect("LBRACE", {"caso", "senao", "RBRACE"})
        cases = []

        while self._check("caso"):
            self._expect("caso", {"SEMICOLON"})
            condition = self._parse_expr_or()
            self._expect("ARROW", {"LBRACE"})
            actions = self._parse_action_block({"caso", "senao", "RBRACE"})
            cases.append(ChooseCase(condition, actions, self._current().line))

        default_actions = self._parse_action_block({"RBRACE"}) if self._match("senao") else None
        self._expect("RBRACE", {"SEMICOLON", "RBRACE", "modo"})
        return ActionChoose(cases, default_actions, start.line if start else self._current().line)

    # Analisa argumentos opcionais.
    def _parse_args(self):
        args = {}
        if self._check("RPAREN"):
            return args

        key, value = self._parse_arg()
        if key:
            args[key] = value
        while self._match("COMMA"):
            key, value = self._parse_arg()
            if key:
                args[key] = value
        return args

    # Analisa um argumento nomeado.
    def _parse_arg(self):
        key = self._expect("IDENT", {"ASSIGN", "RPAREN"})
        self._expect("ASSIGN", VALUE_START_TOKENS | {"RPAREN"})
        return (key.lexeme if key else ""), self._parse_value()

    # Analisa um valor.
    def _parse_value(self):
        tok = self._current()
        if self._match("STRING"):
            return Value("string", tok.lexeme, tok.line)
        if self._match("NUMBER"):
            return Value("number", self._parse_number(tok.lexeme), tok.line)
        if self._match("BOOLEAN"):
            return Value("boolean", tok.lexeme == "true", tok.line)
        if self._match("DURATION"):
            return Value("duration", self._duration_from_lexeme(tok.lexeme, tok.line), tok.line)
        if self._match("TIME"):
            return Value("time", tok.lexeme, tok.line)
        if self._match("ENTITY_ID"):
            return Value("entity", EntityRef(tok.lexeme, True, tok.line), tok.line)
        if self._match("IDENT"):
            return Value("ident", tok.lexeme, tok.line)
        if self._match("LBRACKET"):
            return self._parse_list_value(tok.line)
        if self._match("LBRACE"):
            return self._parse_map_value(tok.line)

        self._error_at(tok, "valor invalido")
        return Value("invalid", None, tok.line)

    # Analisa uma lista como valor.
    def _parse_list_value(self, line):
        values = []
        if not self._check("RBRACKET"):
            values.append(self._parse_value())
            while self._match("COMMA"):
                values.append(self._parse_value())
        self._expect("RBRACKET", {"COMMA", "RPAREN", "SEMICOLON"})
        return Value("list", values, line)

    # Analisa um mapa como valor.
    def _parse_map_value(self, line):
        items = {}
        if not self._check("RBRACE"):
            key, value = self._parse_map_item()
            if key:
                items[key] = value
            while self._match("COMMA"):
                key, value = self._parse_map_item()
                if key:
                    items[key] = value
        self._expect("RBRACE", {"COMMA", "RPAREN", "SEMICOLON"})
        return Value("map", items, line)

    # Analisa um item do mapa.
    def _parse_map_item(self):
        key = self._expect("IDENT", {"COLON", "RBRACE"})
        self._expect("COLON", VALUE_START_TOKENS | {"RBRACE"})
        return (key.lexeme if key else ""), self._parse_value()

    # Analisa uma referencia de entidade.
    def _parse_entity_ref(self):
        tok = self._expect_any({"IDENT", "ENTITY_ID"}, {"SEMICOLON", "RPAREN"})
        if not tok:
            return EntityRef("", False, self._current().line)
        return EntityRef(tok.lexeme, tok.type == "ENTITY_ID", tok.line)

    # Analisa um valor de estado.
    def _parse_state_value(self):
        tok = self._current()
        if self._match("STATE") or self._match("STRING") or self._match("IDENT"):
            return tok.lexeme
        if self._match("NUMBER"):
            return self._parse_number(tok.lexeme)
        self._error_at(tok, "estado invalido")
        return tok.lexeme

    # Analisa uma duracao.
    def _parse_duration(self):
        tok = self._expect("DURATION", {"SEMICOLON", "RPAREN"})
        if not tok:
            return Duration(0, "s", self._current().line)
        return self._duration_from_lexeme(tok.lexeme, tok.line)

    # Converte o texto da duracao em objeto.
    def _duration_from_lexeme(self, lexeme, line):
        for unit in ("ms", "min", "s", "h", "d"):
            if lexeme.endswith(unit):
                return Duration(float(lexeme[:-len(unit)]), unit, line)
        return Duration(float(lexeme), "s", line)

    # Converte numero para int ou float.
    def _parse_number(self, lexeme):
        return float(lexeme) if "." in lexeme else int(lexeme)

    # Retorna o token atual.
    def _current(self):
        return self.tokens[self.pos]

    # Avanca para o proximo token.
    def _advance(self):
        if not self._check("EOF"):
            self.pos += 1
        return self.tokens[self.pos - 1]

    # Consome um token se ele for do tipo esperado.
    def _match(self, token_type):
        if self._check(token_type):
            self._advance()
            return True
        return False

    # Verifica o tipo do token atual.
    def _check(self, token_type):
        return self._current().type == token_type

    # Verifica se o token atual esta em um conjunto.
    def _check_any(self, token_types):
        return self._current().type in token_types

    # Consome um token obrigatorio.
    def _expect(self, token_type, sync):
        if self._check(token_type):
            return self._advance()
        self._error_at(self._current(), f"esperado '{token_type}'")
        self._panic(sync)
        return None

    # Consome um token obrigatorio entre varias opcoes.
    def _expect_any(self, token_types, sync):
        if self._check_any(token_types):
            return self._advance()
        self._error_at(self._current(), f"esperado um de: {', '.join(sorted(token_types))}")
        self._panic(sync)
        return None

    # Registra um erro sintatico.
    def _error_at(self, token, message):
        self.errors.append(f"[Sintatico] Linha {token.line}, Coluna {token.col}: {message}")

    # Avanca ate um ponto seguro de recuperacao.
    def _panic(self, sync):
        while not self._check("EOF") and not self._check_any(sync):
            self._advance()
