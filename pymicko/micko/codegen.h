
#ifndef CODEGEN_H
#define CODEGEN_H

#include "defs.h"

void indent(bool tabs);

int  take_reg(void);
void free_reg(void);
void release_reg(int reg_index);

void gen_str_lab(char *str1, char *str2, bool prefix);
void gen_num_lab(char *str, int num, bool prefix);
void gen_jump_to_str_lab(char *jmp, char *str1, char *str2, bool prefix);
void gen_jump_to_num_lab(char *jmp, char *str, int num, bool prefix);
void gen_glob_var(char *name);
void print_symbol(int index);

void gen_frame_base(void);
void gen_loc_vars(int num);
void gen_function_return(void);
void gen_clear_loc_var(int num);
void gen_function_call(int name_index);
void gen_push(int arg_index);
void gen_reg_save();
void gen_reg_restore();


void gen_cmp(int operand1_index, int operand2_index);
void gen_mov(int input_index, int output_index);

int  gen_arith(int statement, 
                                   int operand1_index, int operand2_index);
int gen_unary_minus(int exp_index);

#endif
