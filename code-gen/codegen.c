#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "codegen.h"
#include "symtab.h"


extern FILE *output;
int free_reg_num = 0;
char invalid_value[] = "???";

// REGISTERS

int take_reg(void) {
  if(free_reg_num > LAST_WORKING_REG) {
    err("Compiler error! No free registers!");
    exit(EXIT_FAILURE);
  }
  return free_reg_num++;
}

void free_reg(void) {
   if(free_reg_num < 1) {
      err("Compiler error! No more registers to free!");
      exit(EXIT_FAILURE);
   }
   else
      set_type(--free_reg_num, NO_TYPE);
}

// Ako je u pitanju indeks registra, oslobodi registar
void free_if_reg(int reg_index) {
  if(reg_index >= 0 && reg_index <= LAST_WORKING_REG)
    free_reg();
}

// LABELS
void gen_sslab(char *str1, char *str2) {
  code("\n@%s%s:", str1, str2);
}

void gen_snlab(char *str, int num) {
  code("\n@%s%d:", str, num);
}


// SYMBOL
void print_symbol(int index) {
  if(index > -1) {
    if(get_kind(index) == VAR) // -n*4(%14)
      code("-%d(%%14)", get_atr1(index) * 4);
    else 
      if(get_kind(index) == PAR) // m*4(%14)
        code("%d(%%14)", 4 + get_atr1(index) *4);
      else
        if(get_kind(index) == LIT)
          code("$%s", get_name(index));
        else //function, reg
          code("%s", get_name(index));
  }
}

// OTHER

void gen_cmp(int op1_index, int op2_index) {
  if(get_type(op1_index) == INT)
    code("\n\t\t\tCMPS \t");
  else
    code("\n\t\t\tCMPU \t");
  print_symbol(op1_index);
  code(",");
  print_symbol(op2_index);
  free_if_reg(op2_index);
  free_if_reg(op1_index);
}

void gen_mov(int input_index, int output_index) {
  code("\n\t\t\tMOV \t");
  print_symbol(input_index);
  code(",");
  print_symbol(output_index);

  //ako se smešta u registar, treba preneti tip 
  if(output_index >= 0 && output_index <= LAST_WORKING_REG)
    set_type(output_index, get_type(input_index));
  free_if_reg(input_index);
}


char* get_arop_stmt(int arop, int type) {
  if ((type < INT) || (type > UINT) || (arop < 0) || (arop >= AROP_NUMBER))
    return invalid_value;
  else
    return arithmetic_operators[arop + (type - 1) * AROP_NUMBER];
}

int get_jump_idx(int relop, bool type) {
  return relop + ((type - 1) * RELOP_NUMBER);
}

char* get_jump_stmt(int jump_idx, bool opp) {
  if ((jump_idx < 0) || (jump_idx >= RELOP_NUMBER * 2))
    return invalid_value;
  else
    if(opp)
      return opp_jumps[jump_idx];
    else        
      return jumps[jump_idx];
} 

