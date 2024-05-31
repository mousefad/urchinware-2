// Dorcas condition parser grammar file for ANTLR4.
// Generate ANTLR4 classes with: antlr4 -Dlanguage=Python3 -no-listener -visitor Condition.g4
// Logic implemented in DorcasVisitor.py
// Parser wrapper for use in Dorcas project: parser.py
grammar Condition;

cond : boolexpr NEWLINE                     # printExpr
     ;

boolexpr : boolexpr 'and' boolexpr          # And
         | boolexpr 'or'  boolexpr          # Or
         | 'not' boolexpr                   # Not
         | value '=' value                  # Equality
         | value '!=' value                 # Inequality
         | value '<' value                  # LessThan
         | value '>' value                  # GreaterThan
         | value '<=' value                 # LessOrEqual
         | value '>=' value                 # GreaterOrEqual
         | value 'like' value               # Like
         | TRUE                             # trueLiteral
         | FALSE                            # falseLiteral
         | '(' boolexpr ')'                 # parens
         ;

value : INT                                 # intLiteral
      | STRING                              # stringLiteral
      | FLOAT                               # floatLiteral
      | IDENT                               # stateVariable
      | TRUE                                # trueValue
      | FALSE                               # falseValue
      | NULL                                # nullValue
      ;

NULL                : 'null' ;
AND                 : 'and' ;
OR                  : 'or' ;
NOT                 : 'not' ;
TRUE                : 'true' ;
FALSE               : 'false' ;
LIKE                : 'like' ;
FLOAT               : DIGIT+ '.' DIGIT*
                    | '.' DIGIT+ 
                    ;
INT                 : [+-]? DIGIT+ ;
STRING              : '\'' ( '\\\'' | ~('\'') )* '\'' ;
IDENT               : LETTER ( LETTER | DIGIT | '_' )* ;
NEWLINE             : '\r'? '\n' ;
WS                  : [ \t\n\r]+ -> skip ;

fragment DIGIT      : [0-9] ;
fragment LETTER     : [a-zA-Z] ;

