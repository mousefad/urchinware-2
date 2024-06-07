# Generated from Condition.g4 by ANTLR 4.13.1
from antlr4 import *
if "." in __name__:
    from .ConditionParser import ConditionParser
else:
    from ConditionParser import ConditionParser

# This class defines a complete generic visitor for a parse tree produced by ConditionParser.

class ConditionVisitor(ParseTreeVisitor):

    # Visit a parse tree produced by ConditionParser#printExpr.
    def visitPrintExpr(self, ctx:ConditionParser.PrintExprContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#LessOrEqual.
    def visitLessOrEqual(self, ctx:ConditionParser.LessOrEqualContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#parens.
    def visitParens(self, ctx:ConditionParser.ParensContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#Or.
    def visitOr(self, ctx:ConditionParser.OrContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#GreaterOrEqual.
    def visitGreaterOrEqual(self, ctx:ConditionParser.GreaterOrEqualContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#trueLiteral.
    def visitTrueLiteral(self, ctx:ConditionParser.TrueLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#Not.
    def visitNot(self, ctx:ConditionParser.NotContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#LessThan.
    def visitLessThan(self, ctx:ConditionParser.LessThanContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#Like.
    def visitLike(self, ctx:ConditionParser.LikeContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#falseLiteral.
    def visitFalseLiteral(self, ctx:ConditionParser.FalseLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#GreaterThan.
    def visitGreaterThan(self, ctx:ConditionParser.GreaterThanContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#And.
    def visitAnd(self, ctx:ConditionParser.AndContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#Equality.
    def visitEquality(self, ctx:ConditionParser.EqualityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#Inequality.
    def visitInequality(self, ctx:ConditionParser.InequalityContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#intLiteral.
    def visitIntLiteral(self, ctx:ConditionParser.IntLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#stringLiteral.
    def visitStringLiteral(self, ctx:ConditionParser.StringLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#floatLiteral.
    def visitFloatLiteral(self, ctx:ConditionParser.FloatLiteralContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#stateVariable.
    def visitStateVariable(self, ctx:ConditionParser.StateVariableContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#trueValue.
    def visitTrueValue(self, ctx:ConditionParser.TrueValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#falseValue.
    def visitFalseValue(self, ctx:ConditionParser.FalseValueContext):
        return self.visitChildren(ctx)


    # Visit a parse tree produced by ConditionParser#nullValue.
    def visitNullValue(self, ctx:ConditionParser.NullValueContext):
        return self.visitChildren(ctx)



del ConditionParser