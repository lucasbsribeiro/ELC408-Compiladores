import re
from dataclasses import dataclass
from typing import List, Optional


KEYWORDS = {
    "automacao",
    "entidades",
    "quando",
    "se",
    "entao",
    "senao",
    "escolha",
    "caso",
    "modo",
    "e",
    "ou",
    "nao",
    "ligar",
    "desligar",
    "esperar",
    "notificar",
    "servico",
    "evento",
    "dispositivo",
    "hora",
    "entre",
    "depois",
    "antes",
    "por",
    "por_do_sol",
    "nascer_do_sol",
    "muda",
    "para",
    "esta",
    "sol",
    "iniciar",
    "parar",
    "finalizar",
    "pressionado",
    "girado",
    "movido",
    "single",
    "restart",
    "queued",
    "parallel",
}

TYPES = {
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

STATE_WORDS = {
    "on",
    "off",
    "disarmed",
    "armed",
    "idle",
    "active",
    "charging",
    "running",
    "standby",
    "playing",
    "desarmado",
    "armado",
    "ligado",
    "desligado",
    "aberto",
    "fechado",
    "movimento",
    "ocupado",
}

BOOLEAN_WORDS = {"true", "false"}

SYMBOLS = {
    "{": "LBRACE",
    "}": "RBRACE",
    "(": "LPAREN",
    ")": "RPAREN",
    "[": "LBRACKET",
    "]": "RBRACKET",
    "=": "ASSIGN",
    ";": "SEMICOLON",
    ",": "COMMA",
    ".": "DOT",
    ":": "COLON",
    "+": "PLUS",
    "-": "MINUS",
}

ENTITY_ID_RE = re.compile(r"[a-z_][a-z0-9_]*\.[a-z0-9_]+")
TIME_RE = re.compile(r"([01]?\d|2[0-3]):[0-5]\d(:[0-5]\d)?")
DURATION_RE = re.compile(r"\d+(?:\.\d+)?(?:ms|s|min|h|d)")
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")


@dataclass
class Token:
    type: str
    lexeme: str
    line: int
    col: int


class Lexer:
    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0
        self.line = 1
        self.col = 1
        self.errors: List[str] = []
        self.servico_ident_left = 0

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
        while True:
            token = self.next_token()
            tokens.append(token)
            if token.type == "EOF":
                break
        return tokens

    def next_token(self) -> Token:
        self._skip_whitespace_and_comments()
        if self._eof():
            return Token("EOF", "", self.line, self.col)

        start_line = self.line
        start_col = self.col
        ch = self._peek()

        if ch == '"':
            return self._read_string(start_line, start_col)

        if ch.isdigit():
            return self._read_number_or_time_or_duration(start_line, start_col)

        if ch.isalpha() or ch == "_":
            return self._read_identifier_or_keyword(start_line, start_col)

        two_chars = ch + self._peek(1)
        comparison_tokens = {
            "==": "OP_EQ",
            "!=": "OP_NE",
            ">=": "OP_GE",
            "<=": "OP_LE",
        }
        if two_chars in comparison_tokens:
            self._advance()
            self._advance()
            return Token(comparison_tokens[two_chars], two_chars, start_line, start_col)

        if ch in {">", "<"}:
            self._advance()
            return Token("OP_GT" if ch == ">" else "OP_LT", ch, start_line, start_col)

        if ch == "-" and self._peek(1) == ">":
            self._advance()
            self._advance()
            return Token("ARROW", "->", start_line, start_col)

        if ch in SYMBOLS:
            self._advance()
            token_type = SYMBOLS[ch]
            if token_type == "LPAREN":
                self.servico_ident_left = 0
            return Token(token_type, ch, start_line, start_col)

        self._advance()
        msg = f"[Lexico] Linha {start_line}, Coluna {start_col}: token invalido '{ch}'"
        self.errors.append(msg)
        return Token("ERROR", ch, start_line, start_col)

    def _skip_whitespace_and_comments(self) -> None:
        while not self._eof():
            ch = self._peek()
            if ch in " \t\r\n":
                self._advance()
                continue
            if ch == "#":
                self._consume_comment()
                continue
            if ch == "/" and self._peek(1) == "/":
                self._advance()
                self._advance()
                self._consume_comment()
                continue
            break

    def _consume_comment(self) -> None:
        while not self._eof() and self._peek() != "\n":
            self._advance()
        if not self._eof() and self._peek() == "\n":
            self._advance()

    def _read_string(self, start_line: int, start_col: int) -> Token:
        self._advance()
        value = []
        while not self._eof():
            ch = self._advance()
            if ch == '"':
                return Token("STRING", "".join(value), start_line, start_col)
            if ch == "\\":
                if self._eof():
                    break
                esc = self._advance()
                if esc == "n":
                    value.append("\n")
                elif esc == "t":
                    value.append("\t")
                elif esc == "\"":
                    value.append("\"")
                elif esc == "\\":
                    value.append("\\")
                else:
                    value.append(esc)
                continue
            if ch == "\n":
                msg = f"[Lexico] Linha {start_line}, Coluna {start_col}: string nao terminada"
                self.errors.append(msg)
                return Token("ERROR", "".join(value), start_line, start_col)
            value.append(ch)
        msg = f"[Lexico] Linha {start_line}, Coluna {start_col}: string nao terminada"
        self.errors.append(msg)
        return Token("ERROR", "".join(value), start_line, start_col)

    def _read_number_or_time_or_duration(self, start_line: int, start_col: int) -> Token:
        text = self.text[self.pos :]
        time_match = TIME_RE.match(text)
        if time_match:
            lexeme = time_match.group(0)
            self._advance_n(len(lexeme))
            return Token("TIME", lexeme, start_line, start_col)

        duration_match = DURATION_RE.match(text)
        if duration_match:
            lexeme = duration_match.group(0)
            self._advance_n(len(lexeme))
            return Token("DURATION", lexeme, start_line, start_col)

        number_match = NUMBER_RE.match(text)
        if number_match:
            lexeme = number_match.group(0)
            self._advance_n(len(lexeme))
            return Token("NUMBER", lexeme, start_line, start_col)

        self._advance()
        msg = f"[Lexico] Linha {start_line}, Coluna {start_col}: numero invalido"
        self.errors.append(msg)
        return Token("ERROR", "", start_line, start_col)

    def _read_identifier_or_keyword(self, start_line: int, start_col: int) -> Token:
        if self.servico_ident_left == 0:
            match = ENTITY_ID_RE.match(self.text[self.pos :])
            if match:
                lexeme = match.group(0)
                self._advance_n(len(lexeme))
                return Token("ENTITY_ID", lexeme, start_line, start_col)

        value = []
        while not self._eof():
            ch = self._peek()
            if ch.isalnum() or ch == "_":
                value.append(self._advance())
            else:
                break
        lexeme = "".join(value)

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

    def _advance(self) -> str:
        ch = self.text[self.pos]
        self.pos += 1
        if ch == "\n":
            self.line += 1
            self.col = 1
        else:
            self.col += 1
        return ch

    def _advance_n(self, count: int) -> None:
        for _ in range(count):
            self._advance()

    def _peek(self, offset: int = 0) -> str:
        idx = self.pos + offset
        if idx >= len(self.text):
            return ""
        return self.text[idx]

    def _eof(self) -> bool:
        return self.pos >= len(self.text)
