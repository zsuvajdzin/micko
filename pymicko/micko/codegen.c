

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "codegen.h"
#include "stack.h"
#include "symtab.h"


extern FILE *output_stream;
extern stack register_stack;

int free_reg_num = 0;


void indent(bool tabs) {
    fprintf(output_stream, "\n");
    if(tabs)
    fprintf(output_stream, "\t\t\t");
}


// REGISTERS

int take_reg(void) {
    if(free_reg_num == LAST_WORKING_REGISTER + 1) {
        printf("\nCompiler error! No free registers!\n");
        exit(EXIT_FAILURE);
    }
    return free_reg_num++;
}

void free_reg(void) {
    set_register_type(free_reg_num, NO_TYPE);
    if(free_reg_num-- < 0) {
        printf("\nCompiler error! No more registers to free!\n");
        exit(EXIT_FAILURE);
    }
}

// Ako je u pitanju indeks registra, oslobodi registar
void release_reg(int reg_index) {
    if(reg_index >= 0 && reg_index <= LAST_WORKING_REGISTER)
        free_reg();
}


// LABELS & JUMPS

void gen_str_lab(char *str1, char *str2, bool prefix) {
    indent(FALSE);
    if(prefix)
        fprintf(output_stream, "@");
    fprintf(output_stream, "%s%s:", str1, str2);
}

void gen_num_lab(char *str, int num, bool prefix) {
    indent(FALSE);
    if(prefix)
        fprintf(output_stream, "@");
    fprintf(output_stream, "%s%d:", str, num);
}

void gen_jump_to_str_lab(char *jmp, char *str1, char *str2, bool prefix) {
    indent(TRUE);
    fprintf(output_stream, "%s\t", jmp);
    if(prefix)
        fprintf(output_stream, "@");
    fprintf(output_stream, "%s%s", str1, str2);
}

void gen_jump_to_num_lab(char *jmp, char *str, int num, bool prefix) {
    indent(TRUE);
    fprintf(output_stream, "%s\t", jmp);
    if(prefix)
        fprintf(output_stream, "@");
    fprintf(output_stream, "%s%d", str, num);
}

void gen_glob_var(char *name) {
    indent(FALSE);
    fprintf(output_stream, "%s:\n\t\t\tWORD\t1", name);
}

// SYMBOL
void print_symbol(int index) {
    if(index > -1) {
        // - n * 4 (%14)
        if(get_kind(index) == LOCAL_VAR)
            fprintf(output_stream, "-%d(%%14)", get_attribute(index) * 4);

        // m * 4 (%14)
        else 
            if(get_kind(index) == PARAMETER)
                fprintf(output_stream, "%d(%%14)", 4 + get_attribute(index) *4);

            // identifier
            else
                if(get_kind(index) == CONSTANT)
                    fprintf(output_stream, "$%s", get_name(index));
                else
                    fprintf(output_stream, "%s", get_name(index));
    }
}


// FUNCTION

void gen_frame_base(void) {
    indent(TRUE);
    fprintf(output_stream, "PUSH\t%%14");
    indent(TRUE);
    fprintf(output_stream, "MOV \t%%15,%%14");
}

void gen_loc_vars(int num) {
    if(num != 0) {
    indent(TRUE);
        fprintf(output_stream, "SUBU\t%%15,$%d,%%15", num * 4);
    }
}

void gen_function_return(void) {
    indent(TRUE);
    fprintf(output_stream, "MOV \t%%14,%%15");
    indent(TRUE);
    fprintf(output_stream, "POP \t%%14");
    indent(TRUE);
    fprintf(output_stream, "RET");
}

void gen_clear_loc_var(int num) {
    if(num > 0) {
    indent(TRUE);
        fprintf(output_stream, "ADDU\t%%15,$%d,%%15", num * 4);
    }
}

void gen_function_call(int name_index) {
    indent(TRUE);
    fprintf(output_stream, "CALL\t");
    print_symbol(name_index);
}

void gen_push(int arg_index) {
    release_reg(arg_index);
    indent(TRUE);
    fprintf(output_stream, "PUSH\t");
    print_symbol(arg_index);
}

void gen_reg_save() {
    int i;
    for(i = 0; i < free_reg_num; i++) {
    indent(TRUE);
        fprintf(output_stream, "PUSH\t%%%d", i);
    }
    push(&register_stack, free_reg_num);
    free_reg_num = 0;
}

void gen_reg_restore() {
    int i;
    free_reg_num = pop(&register_stack);
    for(i = free_reg_num - 1; i >= 0; i--) {
    indent(TRUE);
        fprintf(output_stream, "POP \t%%%d", i);
    }
}


// OTHER

void gen_cmp(int operand1_index, int operand2_index) {
    release_reg(operand1_index);
    release_reg(operand2_index);
    indent(TRUE);
    fprintf(output_stream, "%s\t", cmps[get_type(operand1_index) - 1]);
    print_symbol(operand1_index);
    fprintf(output_stream, ",");
    print_symbol(operand2_index);
}

void gen_mov(int input_index, int output_index) {
    release_reg(input_index);
    indent(TRUE);
    fprintf(output_stream, "MOV \t");
    print_symbol(input_index);
    fprintf(output_stream, ",");
    print_symbol(output_index);

    //ako smestas u registar, prenesi tip 
    if(output_index >= 0 && output_index <= LAST_WORKING_REGISTER)
      set_register_type(output_index, get_type(input_index));
}


// STATEMENTS
int gen_arith(int statement, 
              int operand1_index, int operand2_index) {
    int output_index;
    release_reg(operand1_index);
    release_reg(operand2_index);
    output_index = take_reg();

    indent(TRUE);
    fprintf(output_stream, "%s\t", 
        arithmetic_operators[get_type(operand1_index) - 1][statement]);
    print_symbol(operand1_index);
    fprintf(output_stream, ",");
    print_symbol(operand2_index);
    fprintf(output_stream, ",");
    print_symbol(output_index);

    //tip izraza = tip jednog od operanada (recimo prvog)
    set_register_type(output_index, get_type(operand1_index));
    return output_index;
}

int gen_unary_minus(int exp_index) {
    int output_index = exp_index;
    if(exp_index > LAST_WORKING_REGISTER) {
        output_index = take_reg();
        gen_mov(exp_index, output_index);
    }
    indent(TRUE);
    fprintf(output_stream, "%s\t$0,", 
        arithmetic_operators[get_type(output_index) - 1][SUB_OP]);
    print_symbol(output_index);
    fprintf(output_stream, ",");
    print_symbol(output_index);

    return output_index;
}


