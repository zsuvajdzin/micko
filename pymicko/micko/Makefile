
LEX_SRC = scanner.l
YACC_SRC = parser.y

.PHONY: clean

a.out: lex.yy.c y.tab.c stack.c symtab.c semantic.c codegen.c
	gcc -o $@ $+

lex.yy.c: $(LEX_SRC) y.tab.c
	lex -I $<

y.tab.c: $(YACC_SRC)
	yacc -d -v $<

clean:
	rm -f lex.yy.c
	rm -f y.tab.c
	rm -f y.tab.h
	rm -f y.output
	rm -f a.out
