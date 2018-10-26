

#include <stdio.h>
#include "semantic.h"

extern char char_buffer[CHAR_BUFFER_LENGTH];
extern int error_count;
extern int line;

// Proverava da li se ime main nalazi u tabeli simbola ili ne, 
// i da li je njen tip 'int'.
void check_main() {
    int index;
    if((index = lookup_symbol("main", FUNCTION)) == -1)
        yyerror("undefined reference to 'main'");
    if(get_type(index) != INT_TYPE)
        warning("return type of 'main' is not int");
}

// Proverava da li su isti tipovi elemenata tabele simbola.
bool check_types(int first_index, int second_index) {
    unsigned t1 = get_type(first_index);
    unsigned t2 = get_type(second_index);
    if(t1 == t2 && t1 != NO_TYPE && t2 != NO_TYPE)
        return TRUE;
    else
        return FALSE;
}

// Proverava da li n-ti argument po tipu odgovara n-tom parametru funkcije
bool check_argument_type(int function_call_index, int arg_index, int arg_num) {
    if(get_param_type(function_call_index, arg_num) == get_type(arg_index))
        return TRUE;
    sprintf(char_buffer, "incompatible type for argument %d in '%s'",
            arg_num, get_name(function_call_index));
    yyerror(char_buffer);
    return FALSE;
}

// Proverava da li broj argumenata poziva funkcije
// odgovara broju parametara funkcije
bool check_arguments_number(int function_call_index, int arg_num) {
    if(get_attribute(function_call_index) == arg_num)
        return TRUE;
    sprintf(char_buffer, "wrong number of arguments to function '%s'",
            get_name(function_call_index));
    yyerror(char_buffer);
    return FALSE;
}
