"""
Lexical structure of the calculator input languages.

Programming languges and related formal notations are
divided into at least three levels of descripton:
lexical, syntactic, and semantic.  The semantic
structure may be further divided into static and
dynamic semantics.

The lexical structure of a programming language is the way
an input text is divided into a individual "tokens" or
"lexemes" like identifiers, operator symbols, and
numeric and string literals.  White space and comments
are not lexemes.  For example, if the input is
"(3 * 5)/x", the lexemes should be
["(", "3", "*", "5", ")", "/", "x" ]

Beware 5-3 can read as '5' followed by '-3'; write it
as 5 - 3.
"""
import io
from typing import Sequence

# We use regular expressions (re) for the patterns that
# match lexemes
import re

# An Enum is a special kind of class used to enumerate
# a finite set of values.
from enum import Enum

import logging
logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


# To the extent possible, we would like to describe
# the lexical structure by some tables that are easily
# edited, rather than details of the procedural code.
# We will make a pattern for each distinct token. These
# are 'raw' strings to make it easier to 'escape' some
# characters that are special in regular expressions.
#
# Conventions:
#   UPPER = token
#   error = error  (name is exactly "error")
#   ignore = comment or whitespace (name is exactly "ignore")
#
#   Note these patterns are for both llcalc.py and rpncalc.py;
#   some of the tokens are used only by one or the other.
#
#   Order matters:  e.g., INT must precede MINUS so that -5
#   is read as one negative integer, not MINUS followed by INT.
#   Keywords like IF must precede general patterns like VAR.
#   error should be the last pattern.
#
class TokenCat(Enum):
    ignore = r"\s+|#.*"   # Whitespace and comments
    # Added for compiler project
    WHILE = "while"
    DO = "do"
    OD = "od"
    IF = "if"
    THEN = "then"
    ELSE = "else"
    FI = "fi"
    READ = "read"
    PRINT = "print"
    SEMI = ";"
    # From original calculator
    INT = r"\-?[0-9]+"
    PLUS = r"\+"
    MINUS = r"-"
    TIMES = r"\*"
    DIV = r"/"
    NEG = r"~"
    ABS = r"@"
    VAR = r"[a-zA-Z_][a-zA-Z_]*"
    LPAREN = r"\("
    RPAREN = r"\)"
    # Relations
    EQ = r"=="
    NE = r"!="
    LE = r"<="
    GE = r">="
    GT = r">"
    LT = r"<"
    # Assignment (must be after == )
    ASSIGN = r"="
    # Error processing
    error = "."           # catch-all for errors
    END = "###SHOULD NOT MATCH###"  # Not really a pattern


def all_token_re() -> str:
    """Create a regular expression that matches ALL of the tokens in TokenCat.
    Pattern will look like
     "(?:\+)|(?:\*)|...|(?:[0-9]+)"
    i.e., each token pattern P will be enclosed in the non-capturing
    group (?:P) and all the groups will be combined as alternatives
    with | .
    """
    anything = "|".join([f"(?:{cat.value})" for cat in TokenCat])
    log.debug(f"Pattern '{anything}' should match anything")
    return anything


TOKENS_PAT = re.compile(all_token_re())


class LexicalError(Exception):
    """Raised when we can't extract tokens from the input"""
    pass


class Token(object):
    """One token from the input stream"""

    def __init__(self, value: any, kind: TokenCat):
        self.value = value
        self.kind = kind

    def __repr__(self) -> str:
        return f"Token('{self.value}', {self.kind})"

    def __str__(self) -> str:
        return repr(self)


END = Token("End of Input", TokenCat.END)


class TokenStream(object):
    """
    Provides the tokens within a stream one-by-one.
    Example usage:
       f = open("my_input_file")
       stream = TokenStream(f)
       while stream.has_more():
           token = stream.take()     # Removes token from front of stream
           lookahead = stream.peek() # Returns token without removing it
           # Do something with the token
    """

    def __init__(self, f: io.IOBase):
        self.file = f
        self.tokens = []
        self._check_fill()
        log.debug("Tokens: {}".format(self.tokens))

    def __str__(self) -> str:
        return "[{}]".format("|".join(self.tokens))

    def _check_fill(self):
        while len(self.tokens) == 0:
            # We could read more than one line before hitting
            # a token, but the loop will be broken if we
            # hit end of file
            line = self.file.readline()
            log.debug(f"Check fill reading line: '{line}'")
            if len(line) == 0:
                # End of file, leave zero tokens in buffer
                break
            self.tokens = lex(line.strip())
            log.debug("Refilled, tokens: {}".format(self.tokens))
            # Note this might also leave zero tokens in buffer,
            # but in that case outer while loop will attempt
            # to refill it until we either get some tokens
            # or hit end of file

    def has_more(self) -> bool:
        """True if there are more tokens in the stream"""
        self._check_fill()
        return len(self.tokens) > 0

    def peek(self) -> Token:
        """Examine next token without consuming it. """
        self._check_fill()
        if len(self.tokens) > 0:
            token = self.tokens[0]
        else:
            token = END
        return token

    def take(self) -> Token:
        """Consume next token"""
        self._check_fill()
        if len(self.tokens) > 0:
            token = self.tokens.pop(0)
        else:
            token = END
        return token


def lex(s: str) -> Sequence[Token]:
    """Break string into a list of Token objects"""
    log.debug(f"Running big regular expression on '{s}'")
    words = TOKENS_PAT.findall(s)
    log.debug(f"Findall returned {words}")
    tokens = []
    for word in words:
        token = classify(word)
        if token.kind == TokenCat.ignore:
            log.debug(f"Skipping {token}")
            continue
        tokens.append(token)
    return tokens


def classify(word: str) -> Token:
    """Convert a textual token into a Token object
    with a value and category.
    """
    log.debug(f"Classifying token '{word}")
    for kind in TokenCat:
        log.debug(f"Checking '{word}' for token class '{kind}'")
        pattern = kind.value
        if re.fullmatch(pattern, word):
            log.debug(f"Classified as {kind}")
            if kind.name == "error":
                raise LexicalError(f"Unrecognized character '{word}'")
            return Token(word, kind)
    raise LexicalError(f"Unrecognized token '{word}'")


###
if __name__ == "__main__":
    # Simple smoke test
    text = io.StringIO("3*(4 + 24)+12")
    tokens = TokenStream(text)
    while tokens.has_more():
        print(f"Token: {tokens.take()}")
        input("Press enter to continue")

