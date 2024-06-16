# Built-in modules
import sys
import os
import logging
import random
import copy

log = logging.getLogger(__name__)

FunctionMap = {
    "random": random.random,
    "random_int": random.randint,
    "random_choice": random.choice,
}


def check_condition(expr):
    try:
        compile(expr, "<string>", "eval")
        return True
    except Exception as e:
        log.error(f"condition does not compile: {expr!r}")
        return False


def evaluate_condition(expr, context, id):
    try:
        if expr is None:
            return False
        context = {} if context is None else copy.copy(context)
        for k, v in FunctionMap.items():
            context[k] = v
        code = compile(expr, "<string>", "eval")
        return eval(code, {}, context)
    except Exception as e:
        log.error(f"failed to evaluate condition for {id}", exc_info=True)
        return False

