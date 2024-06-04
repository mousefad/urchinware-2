GRAMMAR = Condition
G4 = $(GRAMMAR).g4
GEN = $(GRAMMAR).interp 
GEN += $(GRAMMAR)Lexer.interp 
GEN += $(GRAMMAR)Lexer.py 
GEN += $(GRAMMAR)Lexer.tokens 
GEN += $(GRAMMAR)Visitor.py
GEN += $(GRAMMAR)Parser.py 
GEN += $(GRAMMAR).tokens

.PHONY : clean

$(GEN) : $(G4)
	antlr4 -Dlanguage=Python3 -no-listener -visitor $(G4)

clean : 
	rm -f $(GEN)

