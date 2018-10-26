/* Skener za mikroC */

%{
    #include <string.h>
    #include "y.tab.h"
    #include "defs.h"

    int line = 1;
    extern YYSTYPE yylval;
%}

letter                      [_a-zA-Z]
digit                       [0-9]

%%

[ \t]+                      {   /* skip */    }

"int"                       {   yylval = INT_TYPE; return _TYPE;        }
"unsigned"                  {   yylval = UNSIGNED_TYPE; return _TYPE;   }
"if"                        {   return _IF;                             }
"else"                      {   return _ELSE;                           }
"while"                     {   return _WHILE;                          }
"return"                    {   return _RETURN;                         }

{letter}({letter}|{digit})* {
                                yylval = (int)strdup(yytext);
                                return _ID; 
                            }


{digit}{1,5}[uU]            {
                                char *s = strdup(yytext);
                                  //skini slovo "u" sa kraja
                                s[strlen(s)-1] = 0;
                                yylval = (int)s; 
                                return _UNSIGNED_NUMBER; 
                            }

[\-\+]?{digit}{1,5}         {
                                yylval = (int)strdup(yytext);
                                return _INT_NUMBER;
                            }


"("                         {   return _LPAREN;                  }
")"                         {   return _RPAREN;                  }
","                         {   return _COMMA;                   }
"{"                         {   return _LBRACKET;                }
"}"                         {   return _RBRACKET;                }
"="                         {   return _ASSIGN;                  }
";"                         {   return _SEMICOLON;               }
"+"                         {   return _PLUS;                    }
"-"                         {   return _MINUS;                   }
"*"                         {   yylval = TIMES; return _MULOP;   }
"/"                         {   yylval = DIV;   return _MULOP;   }
"||"                        {   return _OR;                      }
"&&"                        {   return _AND;                     }
"<"                         {   yylval = LT; return _RELOP;      }
">"                         {   yylval = GT; return _RELOP;      }
"<="                        {   yylval = LE; return _RELOP;      }
">="                        {   yylval = GE; return _RELOP;      }
"=="                        {   yylval = EQ; return _RELOP;      }
"!="                        {   yylval = NE; return _RELOP;      }


"/*"                        {
                                int in_comment = 1;
                                char c;
                                while(in_comment) {
                                    c = input(); 
                                    if(c == '*') {
                                        char ch = input();
                                        if(ch == '/') in_comment = 0;
                                        else unput(ch);
                                    }
                                    else if(c == '\n') line++;
                                    else if(c == EOF) {
                                        printf("\nERROR (%d): "
                                               "Unterminated comment", line);
                                        in_comment = 0;
                                    }
                                }
                            }

\/\/.*                      {   /* skip */   }

"\n"                        {   line++;    }
.                           {   printf("\nLEXICAL ERROR "
                                       "on character %c (line %d)", 
                                       yytext[0], line);   }

%%

int yywrap() {
    return 1;
}
