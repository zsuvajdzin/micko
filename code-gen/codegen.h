#ifndef CODEGEN_H
#define CODEGEN_H

#include "defs.h"

// funkcije za zauzimanje, oslobadjanje registra
int  take_reg(void);
void free_reg(void);
// oslobadja ako jeste indeks registra
void free_if_reg(int reg_index); 

// generise labelu koja se sastoji od 2 stringa 
// npr: @main_exit
void gen_sslab(char *str1, char *str2);

// generise labelu koja se sastoji 
// od jednog stringa i jednog broja npr: @if0
void gen_snlab(char *str, int num);

// ispisuje simbol (u odgovarajucem obliku) 
// koji se nalazi na datom indeksu u tabeli simbola
void print_symbol(int index);

// generise CMP naredbu, parametri su indeksi operanada u TS-a 
void gen_cmp(int operand1_index, int operand2_index);

// generise MOV naredbu, parametri su indeksi operanada u TS-a 
void gen_mov(int input_index, int output_index);

//vraca string aritmeticke naredbe
char* get_arop_stmt(int arop, int type);
//vraca operaciju uslovnog skoka
char* get_jump_stmt(int jump, bool opp);
//vraca indeks u nizu stringova naredbi skokova
int get_jump_idx(int relop, bool type);

#endif
