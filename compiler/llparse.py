"""
An LL parser for the CIS 211 calculator.
Michal Young, spring 2018, revised winter 2019

LL / recursive descent parsing is one of approach to
parsing syntax of programming languages, including
arithmetic expressions.   I'll describe this more
in a separate document
"""

import context
from compiler.lex import TokenStream, TokenCat
import compiler.expr as expr
from typing import TextIO
import io
import traceback

import logging

logging.basicConfig()
log = logging.getLogger(__name__)
log.setLevel(logging.INFO)


class InputError(Exception):
    """Raised when we can't parse the input"""
    pass


def parse(srcfile: TextIO) -> expr.Expr:
    """Interface function to LL parser of Dumbol"""
    stream = TokenStream(srcfile)
    return _program(stream)


#
# The grammar comes here.  It should follow this ebnf:
#
#  program ::=  block
#  block ::= { stmt }
#  stmt ::=  (assign | loop | ifstmt | printstmt) ';'
#  whilestmt ::= 'while' rel 'do' block 'od'
#  ifstmt ::= 'if' rel 'then' block ['else' block] 'fi'
#  rel ::= exp ('==' | '>=' | '<=' | '<' | '>' ) exp
#  assignment ::=  VAR '=' exp
#  exp ::= term { ('+'|'-') term }
#  term ::= primary { ('*'|'/')  primary }
#  primary ::= VAR | INT | '(' exp ')'
#

# Predictions based on next token:
first = {}
first["ifstmt"] = {TokenCat.IF}
first["whilestmt"] = {TokenCat.WHILE}
first["printstmt"] = {TokenCat.PRINT}
first["assignment"] = {TokenCat.VAR}
first["stmt"] = first["ifstmt"].union(first["whilestmt"], first["assignment"], first["printstmt"])
first["exp"] = {TokenCat.VAR, TokenCat.INT, TokenCat.LPAREN, TokenCat.READ }

# Initial version: Just sums

def require(stream: TokenStream, category: TokenCat, desc: str = "", consume=False):
    """Requires the next token in the stream to match a specified category.
    Consumes and discards it if consume==True.
    """
    if stream.peek().kind != category:
        raise InputError(f"Expecting {desc or category}, but saw {stream.peek()} instead")
    if consume:
        stream.take()
    return


def _program(stream: TokenStream) -> expr.Expr:
    """
    program ::= block
    """
    left = _block(stream)
    require(stream, TokenCat.END)
    return left


def _block(stream: TokenStream) -> expr.Expr:
    """
    block ::= { stmt }
    """
    log.debug(f"Parsing block from token {stream.peek()}")
    if stream.peek().kind not in first["stmt"]:
        return expr.Pass()
    left = _stmt(stream)
    log.debug(f"Starting block with {left}")
    while stream.peek().kind in first["stmt"]:
        right = _stmt(stream)
        log.debug(f"Adding statement to block: {right}")
        left = expr.Seq(left, right)
    return left


def _stmt(stream: TokenStream) -> expr.Expr:
    """
    #  stmt ::=  (assign | loop | ifstmt | printstmt) ';'
    assignment ::= IDENT '=' expression
    """
    if stream.peek().kind is TokenCat.WHILE:
        node = _while(stream)
    elif stream.peek().kind is TokenCat.IF:
        node = _if(stream)
    elif stream.peek().kind is TokenCat.PRINT:
        node = _print(stream)
    elif stream.peek().kind is not TokenCat.VAR:
        raise InputError(f"Expecting identifier at beginning of assignment, got {stream.peek()}")
    else:
        target = expr.Var(stream.take().value)
        if stream.peek().kind is not TokenCat.ASSIGN:
            raise InputError(f"Expecting assignment symbol, got {stream.peek()}")
        stream.take()  # Discard '=' token
        value = _expr(stream)
        node = expr.Assign(target, value)
    # All statements should end with semicolon
    require(stream, TokenCat.SEMI, consume=True)
    return node

def _print(stream: TokenStream) -> expr.Print:
    """printstmt ::= print e ; """
    require(stream, TokenCat.PRINT, consume = True)
    exp = _expr(stream)
    return expr.Print(exp)


def _while(stream: TokenStream) -> expr.While:
    """
    whilestmt ::= 'while' exp 'do' block 'od'
    """
    require(stream, TokenCat.WHILE, consume=True)
    cond = _rel(stream)
    require(stream, TokenCat.DO, consume=True)
    block = _block(stream)
    require(stream, TokenCat.OD, consume=True)
    stmt = expr.While(cond, block)
    return stmt


def _if(stream: TokenStream) -> expr.If:
    require(stream, TokenCat.IF, consume=True)
    cond = _rel(stream)
    require(stream, TokenCat.THEN, consume=True)
    then_block = _block(stream)
    if stream.peek().kind == TokenCat.ELSE:
        require(stream, TokenCat.ELSE, consume=True)
        else_block = _block(stream)
        result = expr.If(cond, then_block, else_block)
    else:
        result = expr.If(cond, then_block, elsepart=expr.Pass())
    require(stream, TokenCat.FI, consume=True)
    return result

# All the comparisons are similar, so we'll
# choose the class based on the token
COMPARISONS = { TokenCat.EQ: expr.EQ,  TokenCat.NE: expr.NE,
                TokenCat.LE: expr.LE, TokenCat.LT: expr.LT,
                TokenCat.GE: expr.GE, TokenCat.GT: expr.GT
              }

def _rel(stream: TokenStream) -> expr.Comparison:
    left = _expr(stream)
    op = stream.take()
    right = _expr(stream)
    if op.kind in COMPARISONS:
        clazz = COMPARISONS[op.kind]
        return clazz(left, right)
    else:
        raise InputError(f"Expecting comparison, saw '{op.value}' instead")


def _expr(stream: TokenStream) -> expr.Expr:
    """
    expr ::= term { ('+'|'-') term }
    """
    log.debug(f"parsing sum starting from token {stream.peek()}")
    left = _term(stream)
    log.debug(f"sum begins with {left}")
    while stream.peek().value in ["+", "-"]:
        op = stream.take()
        log.debug(f"expr addition op {op}")
        right = _term(stream)
        if op.value == "+":
            left = expr.Plus(left, right)
        elif op.value == "-":
            left = expr.Minus(left, right)
        else:
            raise InputError(f"What's that op? {op}")
    return left


def _term(stream: TokenStream) -> expr.Expr:
    """term ::= primary { ('*'|'/')  primary }"""
    left = _primary(stream)
    log.debug(f"term starts with {left}")
    while stream.peek().value in ["*", "/"]:
        op = stream.take()
        right = _primary(stream)
        if op.value == "*":
            left = expr.Times(left, right)
        elif op.value == "/":
            left = expr.Div(left, right)
        else:
            raise InputError(f"Expecting multiplicative op, got {op}")
    return left


def _primary(stream: TokenStream) -> expr.Expr:
    """Unary operations, Constants, Variables,
    input, and parenthesized expressions"""
    log.debug(f"Parsing primary with starting token {stream.peek()}")
    token = stream.take()
    if token.kind is TokenCat.INT:
        log.debug(f"Returning IntConst node from token {token}")
        return expr.IntConst(int(token.value))
    elif token.kind is TokenCat.VAR:
        log.debug(f"Variable {token.value}")
        return expr.Var(token.value)
    elif token.kind is TokenCat.READ:
        log.debug("Read")
        return expr.Read()
    elif token.kind is TokenCat.ABS:
        operand = _primary(stream)
        return expr.Abs(operand)
    elif token.kind is TokenCat.NEG:
        operand = _primary(stream)
        return expr.Neg(operand)
    elif token.kind is TokenCat.LPAREN:
        nested = _expr(stream)
        require(stream, TokenCat.RPAREN, consume=True)
        return nested
    else:
        raise InputError(f"Confused about {token} in expression")

###
# Calculator
###

def calc(text: str):
    """Parse and execute a single line"""
    try:
        exp = parse(io.StringIO(text))
        print(f"{exp} => {exp.eval()}")
    except Exception as e:
        raise e
        log.debug("Exception encountered in calculation, traceback follows")
        log.debug('\n+++'.join(traceback.format_stack()))
        print(f"Oops! {e}")

def llcalc():
    """Interactive calculator interface."""
    txt = input("Expression (return to quit):")
    while len(txt.strip()) > 0:
        calc(txt)
        txt = input("Expression (return to quit):")
    print("Bye! Thanks for the math!")


if __name__ == "__main__":
    llcalc()