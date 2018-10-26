
SRC = scanner
.PHONY: clean

$(SRC): lex.yy.c
	gcc -o $@ $+

lex.yy.c: $(SRC).l
	flex $<

clean:
	rm -f lex.yy.c
	rm -f $(SRC).tab.c
	rm -f $(SRC).tab.h
	rm -f $(SRC)

