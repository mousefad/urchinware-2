# Built-in modules
import sys
import os
import logging

# PIP-installed modues
from antlr4 import *
from antlr4.error.ErrorListener import ErrorListener

# Project modules
from dorcas.condition.ConditionLexer import ConditionLexer
from dorcas.condition.ConditionParser import ConditionParser
from dorcas.condition.visitor import Visitor


log = logging.getLogger(os.path.basename(sys.argv[0]))

class EListener(ErrorListener):
    def __init__(self, condition_str, condition_id):
        self.condition_str = condition_str
        self.condition_id = condition_id

    def syntaxError(self, recognizer, offendingSymbol, line, column, msg, e):
        raise SyntaxError(f"ERROR {msg} at line {line} col {column} in {self.condition_str!r} (from {self.condition_str!r})")

def evaluate_condition(condition_str, state, condition_id):
    try:
        stream = InputStream(condition_str)
        lexer = ConditionLexer(stream)
        token_stream = CommonTokenStream(lexer)
        token_stream.fill()
        parser = ConditionParser(token_stream)
        parser.removeErrorListeners()
        parser.addErrorListener(EListener(condition_str, condition_id))
        tree = parser.boolexpr()
        visitor = Visitor(state)
        return visitor.visit(tree)
    except SyntaxError as e:
        log.error(str(e))
        return False
    except KeyError as e:
        log.error(f"ERROR state var {e} not found in condition {condition_str!r} (from {condition_id})")
        return False
    except Exception as e:
        log.error(f"ERROR: {e} processing condition {condition_str!r} (from {condition_id})")
        return False


