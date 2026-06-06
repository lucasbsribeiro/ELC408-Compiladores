import re


KEYWORDS = {
    "automacao", "entidades", "quando", "se", "entao", "senao", "escolha",
    "caso", "modo", "e", "ou", "nao", "ligar", "desligar", "esperar",
    "notificar", "servico", "evento", "dispositivo", "hora", "entre",
    "depois", "antes", "por", "por_do_sol", "nascer_do_sol", "muda",
    "para", "esta", "sol", "iniciar", "parar", "finalizar",
    "pressionado", "girado", "movido", "single", "restart", "queued",
    "parallel",
}

TYPES = {
    "luz", "sensor", "interruptor", "alarme", "timer",
    "clima", "midia", "cortina", "cena", "grupo",
}

STATE_WORDS = {
    "on", "off", "disarmed", "armed", "idle", "active", "charging",
    "running", "standby", "playing", "desarmado", "armado", "ligado",
    "desligado", "aberto", "fechado", "movimento", "ocupado",
}

BOOLEAN_WORDS = {"true", "false"}

SYMBOLS = {
    "{": "LBRACE", "}": "RBRACE", "(": "LPAREN", ")": "RPAREN",
    "[": "LBRACKET", "]": "RBRACKET", "=": "ASSIGN", ";": "SEMICOLON",
    ",": "COMMA", ".": "DOT", ":": "COLON", "+": "PLUS", "-": "MINUS",
}

OPERATORS = {
    "==": "OP_EQ", "!=": "OP_NE", ">=": "OP_GE",
    "<=": "OP_LE", ">": "OP_GT", "<": "OP_LT", "->": "ARROW",
}

ENTITY_ID_RE = re.compile(r"[a-z_][a-z0-9_]*\.[a-z0-9_]+")
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
TIME_RE = re.compile(r"([01]?\d|2[0-3]):[0-5]\d(:[0-5]\d)?")
DURATION_RE = re.compile(r"\d+(?:\.\d+)?(?:ms|s|min|h|d)")
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


class Token:
    # Guarda um token reconhecido pelo lexer.
    def __init__(self, type, lexeme, line, col):
        self.type = type
        self.lexeme = lexeme
        self.line = line
        self.col = col


class Lexer:
    # Prepara o lexer para ler o texto de entrada.
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.errors = []
        self.servico_ident_left = 0

    # Gera todos os tokens ate o fim do arquivo.
    def tokenize(self):
        tokens = []
        while True:
            token = self.next_token()
            tokens.append(token)
            if token.type == "EOF":
                return tokens

    # Le o proximo token da entrada.
    def next_token(self):
        self._skip_whitespace_and_comments()
        if self._eof():
            return Token("EOF", "", self.line, self.col)

        start_line, start_col = self.line, self.col
        ch = self._peek()

        if ch == '"':
            return self._read_string(start_line, start_col)
        if ch.isdigit():
            return self._read_number_time_or_duration(start_line, start_col)
        if ch.isalpha() or ch == "_":
            return self._read_word(start_line, start_col)

        token = self._read_operator_or_symbol(start_line, start_col)
        if token:
            return token

        self._advance()
        self.errors.append(f"[Lexico] Linha {start_line}, Coluna {start_col}: token invalido '{ch}'")
        return Token("ERROR", ch, start_line, start_col)

    # Ignora espacos e comentarios.
    def _skip_whitespace_and_comments(self):
        while not self._eof():
            ch = self._peek()
            if ch in " \t\r\n":
                self._advance()
            elif ch == "#":
                self._consume_comment()
            elif ch == "/" and self._peek(1) == "/":
                self._advance()
                self._advance()
                self._consume_comment()
            else:
                return

    # Consome texto ate o fim da linha.
    def _consume_comment(self):
        while not self._eof() and self._peek() != "\n":
            self._advance()
        if not self._eof():
            self._advance()

    # Le uma string com escapes simples.
    def _read_string(self, start_line, start_col):
        self._advance()
        value = []

        while not self._eof():
            ch = self._advance()
            if ch == '"':
                return Token("STRING", "".join(value), start_line, start_col)
            if ch == "\\":
                value.append(self._read_escape())
                continue
            if ch == "\n":
                break
            value.append(ch)

        self.errors.append(f"[Lexico] Linha {start_line}, Coluna {start_col}: string nao terminada")
        return Token("ERROR", "".join(value), start_line, start_col)

    # Le um caractere escapado.
    def _read_escape(self):
        if self._eof():
            return ""
        esc = self._advance()
        return {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(esc, esc)

    # Le numero, horario ou duracao.
    def _read_number_time_or_duration(self, start_line, start_col):
        for token_type, regex in (("TIME", TIME_RE), ("DURATION", DURATION_RE), ("NUMBER", NUMBER_RE)):
            match = regex.match(self.text, self.pos)
            if match:
                lexeme = match.group(0)
                self._advance_n(len(lexeme))
                return Token(token_type, lexeme, start_line, start_col)

        self._advance()
        self.errors.append(f"[Lexico] Linha {start_line}, Coluna {start_col}: numero invalido")
        return Token("ERROR", "", start_line, start_col)

    # Le identificador, palavra-chave, estado ou entity_id.
    def _read_word(self, start_line, start_col):
        if self.servico_ident_left == 0:
            match = ENTITY_ID_RE.match(self.text, self.pos)
            if match:
                return self._token_from_match("ENTITY_ID", match, start_line, start_col)

        match = IDENT_RE.match(self.text, self.pos)
        lexeme = match.group(0)
        self._advance_n(len(lexeme))

        if lexeme in KEYWORDS or lexeme in TYPES:
            if lexeme == "servico":
                self.servico_ident_left = 2
            return Token(lexeme, lexeme, start_line, start_col)
        if lexeme in BOOLEAN_WORDS:
            return Token("BOOLEAN", lexeme, start_line, start_col)
        if lexeme in STATE_WORDS:
            return Token("STATE", lexeme, start_line, start_col)
        if self.servico_ident_left > 0:
            self.servico_ident_left -= 1
        return Token("IDENT", lexeme, start_line, start_col)

    # Le operadores e simbolos de pontuacao.
    def _read_operator_or_symbol(self, start_line, start_col):
        for text, token_type in OPERATORS.items():
            if self.text.startswith(text, self.pos):
                self._advance_n(len(text))
                return Token(token_type, text, start_line, start_col)

        ch = self._peek()
        if ch in SYMBOLS:
            self._advance()
            if SYMBOLS[ch] == "LPAREN":
                self.servico_ident_left = 0
            return Token(SYMBOLS[ch], ch, start_line, start_col)
        return None

    # Cria token a partir de regex e avanca a posicao.
    def _token_from_match(self, token_type, match, line, col):
        lexeme = match.group(0)
        self._advance_n(len(lexeme))
        return Token(token_type, lexeme, line, col)

    # Avanca um caractere.
    def _advance(self):
        ch = self.text[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    # Avanca varios caracteres.
    def _advance_n(self, count):
        for _ in range(count):
            self._advance()

    # Olha um caractere sem consumir.
    def _peek(self, offset=0):
        idx = self.pos + offset
        return "" if idx >= len(self.text) else self.text[idx]

    # Diz se chegou ao fim da entrada.
    def _eof(self):
        return self.pos >= len(self.text)
