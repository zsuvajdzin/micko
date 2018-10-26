
/* Parser za microC */

%{
    #include <stdio.h>
    #include "defs.h"
    #include "symtab.h"
    #include "stack.h"
    #include "semantic.h"
    #include "codegen.h"

    int yyparse(void);
    int yylex(void);
    int yyerror(char *s);
    void warning(char *s);

    extern int line;
    char char_buffer[CHAR_BUFFER_LENGTH];
    FILE *output_stream;

    int level = GLOBAL_LEVEL;
    int var_num = 0;
    int arg_num = 0;
    int par_num = 0;
    int function_index = -1;
    int function_call_index = -1;
    int lab_num;
    int false_lab_num = -1;

    stack label_stack;
    stack register_stack;
    stack argument_stack;
    stack argument_number_stack;
    stack function_call_stack;

%}


%token _TYPE
%token _IF
%token _ELSE
%token _WHILE
%token _RETURN
%token _ID
%token _INT_NUMBER
%token _UNSIGNED_NUMBER
%token _LPAREN
%token _RPAREN
%token _COMMA
%token _LBRACKET
%token _RBRACKET
%token _ASSIGN
%token _SEMICOLON
%token _PLUS
%token _MINUS
%token _MULOP
%token _OR
%token _AND
%token _RELOP


%%

program
    :   variable_list function_list
            {
                check_main();
            }

    |   function_list
            {
                check_main();

            }
    ;

variable_list
    :   variable _SEMICOLON
    |   variable_list variable _SEMICOLON
    ;

variable
    :   type _ID
            {
                switch(level) {
                  case GLOBAL_LEVEL : {
                      $$ = try_to_insert_id((char *)$2, GLOBAL_VAR, $1);
                      gen_glob_var((char *)$2);
                  }; break;
                  case LOCAL_LEVEL : {
                      $$ = try_to_insert_id((char *)$2, LOCAL_VAR, $1);
                      var_num++;
                      set_attribute($$, var_num);
                  }; break;
                  case PARAMETER_LEVEL : {
                      $$ = try_to_insert_id((char *)$2, PARAMETER, $1);
                      par_num++;
                      set_attribute($$, par_num);
                      set_param_type(function_index,par_num,get_type($$));
                  }; break;
                }
            }
    ;

type
    :   _TYPE
            {
                $$ = $1;
            }
    ;

function_list
    :   function
    |   function_list function
    ;

function
    :   type _ID
            {
                function_index = try_to_insert_id((char *)$2, FUNCTION, $1);
                gen_str_lab((char *)$2, "", FALSE);
                gen_frame_base();
            }
        _LPAREN
            {
                level = PARAMETER_LEVEL;
                par_num = 0;
            }
        parameters _RPAREN
            {
                // postavi broj parametara funkcije
                set_attribute(function_index, par_num);
                level = LOCAL_LEVEL;
                var_num = 0;
            }
        body
            {
                // izbaci iz tabele simbola sve lokalne simbole za funkciju
                clear_symbols(function_index + 1);
                level = GLOBAL_LEVEL;

                gen_str_lab((char *)$2, "_exit", TRUE);
                gen_function_return();
            }
    ;

parameters
    :   /* empty */
    |   parameter_list
    ;

parameter_list
    :   variable
    |   parameter_list _COMMA variable
    ;

body
    :   _LBRACKET variable_list
            {
                gen_loc_vars(var_num);
                gen_str_lab(get_name(function_index), "_body", TRUE);
            }
        statement_list _RBRACKET

    |   _LBRACKET
            {
                gen_str_lab(get_name(function_index), "_body", TRUE);
            }
        statement_list _RBRACKET
    ;

statement_list
    :   /* empty */
    |   statement_list statement
    ;

statement
    :   assignment_statement
    |   function_call_statement
    |   if_statement
    |   while_statement
    |   return_statement
    |   compound_statement
    ;

assignment_statement
    :   _ID
            {
                if( ($$ = lookup_symbol((char *)$1,
                                        GLOBAL_VAR|LOCAL_VAR|PARAMETER)) == -1 )
                    yyerror("invalid lvalue in assignment");
            }
        _ASSIGN num_exp _SEMICOLON
            {
                if(!check_types($2, $4))
                    yyerror("incompatible types in assignment");
                gen_mov($4, $2);
            }
    ;

num_exp
    :   mul_exp

    |   num_exp _PLUS mul_exp
            {
                if(!check_types($1, $3))
                    yyerror("invalid operands to binary +");
                $$ = gen_arith(ADD_OP, $1, $3);
            }

    |   num_exp _MINUS mul_exp
            {
                if(!check_types($1, $3))
                    yyerror("invalid operands to binary -");
                $$ = gen_arith(SUB_OP, $1, $3);
            }
    ;

mul_exp
    :   exp

    |   mul_exp _MULOP exp
            {
                switch($2) {
                  case TIMES  :   {
                      if(!check_types($1, $3))
                          yyerror("invalid operands to binary *");
                      $$ = gen_arith(MUL_OP, $1, $3);
                  }; break;
                  case DIV    :   {
                      if(!check_types($1, $3))
                          yyerror("invalid operands to binary /");
                      $$ = gen_arith(DIV_OP, $1, $3);
                  }; break;
                }
            }
    ;

exp
    :   constant

    |   _ID
            {
                if( ($$ = lookup_symbol((char *)$1,
                                        GLOBAL_VAR|LOCAL_VAR|PARAMETER)) == -1){
                    sprintf(char_buffer, "'%s' undeclared", (char *)$1);
                    yyerror(char_buffer);
                }
            }

    |   function_call
            {
                //povratna vrednost funkcije se smesta u prvi slobodan registar
                $$ = take_reg();
                gen_mov(FUNCTION_REGISTER, $$);
            }

    |   _LPAREN num_exp _RPAREN
            {
                $$ = $2;
            }

    |   _PLUS exp
            {
                if($2 > -1 && get_type($2) == UNSIGNED_TYPE)
                    warning("sign used with unsigned expression");
                $$ = $2;
            }

    |   _MINUS exp
            {
                int reg = gen_unary_minus($2);
                if($2 > -1 && get_type($2) == UNSIGNED_TYPE)
                    warning("sign used with unsigned expression");
                $$ = reg;
            }
    ;

constant
    :   _INT_NUMBER
            {
                $$ = try_to_insert_constant((char *)$1, INT_TYPE);
            }

    |   _UNSIGNED_NUMBER
            {
                $$ = try_to_insert_constant((char *)$1, UNSIGNED_TYPE);
            }
    ;

function_call
    :   _ID
            {
                int index;
                if( (index = lookup_symbol((char *)$1, FUNCTION)) == -1 ) {
                    sprintf(char_buffer, "'%s' is not a function", (char *)$1);
                    yyerror(char_buffer);
                }
                push(&function_call_stack, function_call_index);
                function_call_index = index;
                gen_reg_save();
            }
        _LPAREN arguments _RPAREN
            {
                check_arguments_number(function_call_index, arg_num);
                
                gen_function_call(function_call_index);
                gen_clear_loc_var(arg_num);
                
                arg_num = pop(&argument_number_stack);
                
                //postavi tip povratne vrednosti funkcije u %13
                set_register_type(FUNCTION_REGISTER, 
                                  get_type(function_call_index));
                function_call_index = pop(&function_call_stack);
                gen_reg_restore();
                
                //povratna vrednost funkcije se uvek nalazi u %13
                $$ = FUNCTION_REGISTER;
            }
    ;

arguments
    :   /* empty */
            {
                //broj dosadasnjih argumenata poziva funkcije smesti na stek
                push(&argument_number_stack, arg_num);
                arg_num = 0;
            }

    |   argument_list
            {
                int args = arg_num;
                while(args-- > 0)
                    gen_push(pop(&argument_stack));
            }
    ;

argument_list
    :   num_exp
            {
                // broj dosadasnjih argumenata poziva funkcije smesti na stek
                push(&argument_number_stack, arg_num);
                arg_num = 1;
                check_argument_type(function_call_index, $1, arg_num);
                push(&argument_stack, $1);
            }

    |   argument_list _COMMA num_exp
            {
                arg_num++;
                check_argument_type(function_call_index, $3, arg_num);
                push(&argument_stack, $3);
            }
    ;

function_call_statement
    :   function_call _SEMICOLON
    ;

if_statement
    :   if_part
            {
                gen_num_lab("exit", lab_num, TRUE);
            }

    |   if_part _ELSE
            {
                push(&label_stack, lab_num);
            }
        statement
            {
                gen_num_lab("exit", pop(&label_stack), TRUE);
            }
    ;

if_part
    :   _IF _LPAREN
            {
                lab_num = ++false_lab_num;
                gen_num_lab("if", lab_num, TRUE);
            }
        log_exp
            {
                gen_jump_to_num_lab(opposite_jumps[$4],
                                    "false", false_lab_num, TRUE);
                gen_num_lab("true", lab_num, TRUE);
                push(&label_stack, false_lab_num);
                push(&label_stack, lab_num);
            }
        _RPAREN statement
            {
                lab_num = pop(&label_stack);
                gen_jump_to_num_lab(unconditional_jump, 
                                    "exit", lab_num, TRUE);
                gen_num_lab("false", pop(&label_stack), TRUE);
            }
    ;

log_exp
    :   and_exp

    |   log_exp _OR
            {
                gen_jump_to_num_lab(jumps[$1], "true", lab_num, TRUE);
                gen_num_lab("false", false_lab_num, TRUE);
                false_lab_num++;
            }
        and_exp
            {
                $$ = $4;    // prenosi konstantu za uslovni skok
            }
    ;

and_exp
    :   rel_exp

    |   and_exp _AND
            {
                gen_jump_to_num_lab(opposite_jumps[$1],
                                    "false", false_lab_num, TRUE);
            }
        rel_exp
            {
                $$ = $4;    // prenosi konstantu za uslovni skok
            }
    ;

rel_exp
    :   num_exp _RELOP num_exp
            {
                if(!check_types($1, $3))
                    yyerror("invalid operands to relational operator");
                gen_cmp($1, $3);
                // prenosi konstantu za uslovni skok
                $$ = $2 + ((get_type($1)-1) * RELOP_NUMBER);
                // oduzima se 1 posto je INT_TYPE = 1, a UNSIGNED_TYPE = 2
            }
    ;

while_statement
    :   _WHILE _LPAREN
            {
                lab_num = ++false_lab_num;
                gen_num_lab("while", lab_num, TRUE);
            }
        log_exp
            {
                gen_jump_to_num_lab(opposite_jumps[$4],
                                    "false", false_lab_num, TRUE);
                gen_num_lab("true", lab_num, TRUE);
                push(&label_stack, false_lab_num);
                push(&label_stack, lab_num);
            }
        _RPAREN statement
            {
                lab_num = pop(&label_stack);
                gen_jump_to_num_lab(unconditional_jump, 
                                    "while", lab_num, TRUE);
                gen_num_lab("false", pop(&label_stack), TRUE);
                gen_num_lab("exit", lab_num, TRUE);
            }
    ;

return_statement
    :   _RETURN num_exp _SEMICOLON
            {
                if(!check_types(function_index, $2))
                    yyerror("incompatible types in return");
                // vrednost return izraza se prebacuje u
                // registar koji je namenjen povratnoj vrednosti funkcije
                gen_mov($2, FUNCTION_REGISTER);
                gen_jump_to_str_lab(unconditional_jump,
                                    get_name(function_index), "_exit", TRUE);
            }
    ;

compound_statement
    :   _LBRACKET statement_list _RBRACKET
    ;


%%


    int yyerror(char *s) {
        fprintf(stderr, "\nERROR (%d): %s", line, s);
        return 0;
    }

void warning(char *s) {
    fprintf(stderr, "\nWARNING (%d): %s", line, s);
}

int main() {
    printf("\nSTART\n");
    init_symtab();
    init_stack(&argument_stack);
    init_stack(&argument_number_stack);
    init_stack(&label_stack);
    init_stack(&function_call_stack);
    init_stack(&register_stack);
    output_stream = fopen("output.asm", "w+");

    yyparse();
    //print_symtab();

    clear_symtab();
    fclose(output_stream);
    printf("\nSTOP\n");
    return 0;
}

