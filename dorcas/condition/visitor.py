import sys
import os
import logging
import re

from antlr4 import *
from dorcas.condition.ConditionParser import ConditionParser
from dorcas.condition.ConditionVisitor import *


log = logging.getLogger(os.path.basename(sys.argv[0]))


class Visitor(ConditionVisitor):
    def __init__(self, state={}):
        self.state = state

    def visitFalseLiteral(self, ctx:ConditionParser.FalseLiteralContext):
        return False

    def visitTrueLiteral(self, ctx:ConditionParser.TrueLiteralContext):
        return True

    def visitIntLiteral(self, ctx:ConditionParser.IntLiteralContext):
        return int(ctx.start.text)

    def visitTrueValue(self, ctx:ConditionParser.TrueValueContext):
        return True

    def visitFalseValue(self, ctx:ConditionParser.FalseValueContext):
        return False

    def visitNullValue(self, ctx:ConditionParser.NullValueContext):
        return None

    def visitFloatLiteral(self, ctx:ConditionParser.FloatLiteralContext):
        return float(ctx.start.text)

    def visitStringLiteral(self, ctx:ConditionParser.StringLiteralContext):
        text = ctx.start.text
        # remove leading and trailing "'", and de-escape single quotes
        return text[1:-1].replace("\\'", "'")

    def visitStateVariable(self, ctx:ConditionParser.StateVariableContext):
        return self.state.get(ctx.start.text)

    def visitNot(self, ctx:ConditionParser.NotContext):
        return not self.visitChildren(ctx)

    def visitAnd(self, ctx:ConditionParser.AndContext):
        left = self.visit(ctx.boolexpr(0))
        right = self.visit(ctx.boolexpr(1))
        return left and right

    def visitOr(self, ctx:ConditionParser.OrContext):
        left = self.visit(ctx.boolexpr(0))
        right = self.visit(ctx.boolexpr(1))
        return left or right

    def visitLike(self, ctx:ConditionParser.LikeContext):
        left = str(self.visit(ctx.value(0)))
        pat = re.escape(str(self.visit(ctx.value(1))))
        pat = pat.replace("%", ".*") + "$"
        return re.match(pat, left) is not None

    def visitEquality(self, ctx:ConditionParser.EqualityContext):
        left = self.visit(ctx.value(0))
        right = self.visit(ctx.value(1))
        return left == right

    def visitInequality(self, ctx:ConditionParser.InequalityContext):
        left = self.visit(ctx.value(0))
        right = self.visit(ctx.value(1))
        return left != right

    def visitLessThan(self, ctx:ConditionParser.LessThanContext):
        left = self.visit(ctx.value(0))
        right = self.visit(ctx.value(1))
        return left < right

    def visitLessOrEqual(self, ctx:ConditionParser.LessOrEqualContext):
        left = self.visit(ctx.value(0))
        right = self.visit(ctx.value(1))
        return left <= right

    def visitGreaterThan(self, ctx:ConditionParser.GreaterThanContext):
        left = self.visit(ctx.value(0))
        right = self.visit(ctx.value(1))
        return left > right

    def visitGreaterOrEqual(self, ctx:ConditionParser.GreaterOrEqualContext):
        left = self.visit(ctx.value(0))
        right = self.visit(ctx.value(1))
        return left >= right

    def visitParens(self, ctx:ConditionParser.ParensContext):
        return self.visit(ctx.boolexpr())

