%option noyywrap yylineno
%{
  union {
    int i;
    char *s;
  } yylval;
   
  enum tokens { _TYPE = 1, _IF, _ELSE, _RETURN, 
                _LPAREN, _RPAREN, _LBRACKET, _RBRACKET, 
                _SEMICOLON, _ASSIGN, _AROP, _RELOP, _ID, 
                _INT_NUMBER, _UINT_NUMBER };
  char *token_strings[] = { "NONE", "_TYPE", "_IF", 
                "_ELSE", "_RETURN", "_LPAREN","_RPAREN", 
                "_LBRACKET", "_RBRACKET", "_SEMICOLON", 
                "_ASSIGN", "_AROP", "_RELOP", "_ID", 
                "_INT_NUMBER", "_UINT_NUMBER" };
   
  enum values { ADD, SUB, LT, EQ, INT, UINT};
  char *value_strings[] = { "ADD", "SUB", 
                            "LT",  "EQ", 
                            "INT", "UINT" };
%}

%%

[ \t\n]+       { /* skip */ }

"if"           { return _IF; }
"else"         { return _ELSE; }
"return"       { return _RETURN; }

"int"          { yylval.i = INT;  return _TYPE; }
"unsigned"     { yylval.i = UINT; return _TYPE; }

"("            { return _LPAREN; }
")"            { return _RPAREN; }
"{"            { return _LBRACKET; }
"}"            { return _RBRACKET; }
";"            { return _SEMICOLON; }
"="            { return _ASSIGN; }

"+"            { yylval.i = ADD; return _AROP; }
"-"            { yylval.i = SUB; return _AROP; }

"<"            { yylval.i = LT; return _RELOP; }
"=="           { yylval.i = EQ; return _RELOP; }

[a-zA-Z][a-zA-Z0-9]*  { yylval.s = yytext; 
                        return _ID; }
[+-]?[0-9]{1,10}      { yylval.s = yytext; 
                        return _INT_NUMBER;}
[0-9]{1,10}[uU]       { yylval.s = yytext; 
                        return _UINT_NUMBER;}

\/\/.*         { /* skip */ }
.              { printf("line %d: LEXICAL ERROR "
                 "on char %c\n",yylineno, *yytext);}

%%

int main() {
  int tok;
  while(tok = yylex()) {
    printf("%s", token_strings[tok]);
    switch(tok) {
      case _ID: 
      case _INT_NUMBER: 
      case _UINT_NUMBER:
        printf(": %s", yylval.s); break;
      case _AROP: 
      case _RELOP: 
      case _TYPE:
        printf(": %s", value_strings[yylval.i]);break;
    }
    printf("\n");
  }
}
