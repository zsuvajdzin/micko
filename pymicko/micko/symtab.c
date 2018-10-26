
#include <ctype.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "defs.h"
#include "symtab.h"


SYMBOL_ENTRY symbol_table[SYMBOL_TABLE_LENGTH];
extern char char_buffer[CHAR_BUFFER_LENGTH];

int first_empty = 0;


// Vraca indeks prvog sledeceg praznog elementa.
int get_next_empty_element(void) {
    if(first_empty < SYMBOL_TABLE_LENGTH)
        return first_empty++;
    else {
        printf("\nSymbol table overflow!\n");
        exit(EXIT_FAILURE);
        return 0;
    }
}

// Ubacuje simbol sa datom oznakom simbola i tipom simbola 
// i vraca indeks ubacenog elementa u tabeli simbola ili -1.
int insert_symbol(char *name, unsigned kind, unsigned type) {
    int index = get_next_empty_element();
    symbol_table[index].name = name;
    symbol_table[index].kind = kind;
    symbol_table[index].type = type;
    return index;
}

// Proverava da li se simbol vec nalazi u tabeli simbola,
// ako se ne nalazi ubacuje ga, ako se nalazi ispisuje gresku.
// Vraca indeks elementa u tabeli simbola.
int try_to_insert_id(char *name, unsigned kind, unsigned type) {
    int index;
    if( (index = lookup_symbol(name, kind)) == -1 )
        index = insert_symbol(name, kind, type);
    else {
        sprintf(char_buffer, "redefinition of '%s'", name);
        yyerror(char_buffer);
    }
    return index;
}

// Ubacuje konstantu u tabelu simbola (ako vec ne postoji).
int try_to_insert_constant(char *str, unsigned type) {
    int index;
    if( (index = lookup_constant(str, type)) == -1 ) {
        // provera opsega za konstante
        long number = atol(str);
        switch(type) {
          case UNSIGNED_TYPE : {
              if( number < 0 || number >= (1L << TYPE_BIT_SIZE) )
                  yyerror("constant out of range");
          }; break;
          case INT_TYPE : {
              if( number < (-(1L << (TYPE_BIT_SIZE - 1))) 
                  || number >= ((1L << (TYPE_BIT_SIZE - 1))))    
                  yyerror("constant out of range");
          }; break;
        }
        index = insert_symbol(str, CONSTANT, type);
    }
    return index;
}

// Vraca indeks pronadjenog simbola ili vraca -1.
int lookup_symbol(char *name, unsigned kind) {
    int i;
    for(i = first_empty - 1; i > FUNCTION_REGISTER; i--) {
        if(strcmp(symbol_table[i].name, name) == 0 
           && symbol_table[i].kind & kind)
            return i;
    }
    return -1;
}

// Vraca indeks pronadjenog simbola (konstante) ili vraca -1.
int lookup_constant(char *name, unsigned type) {
    int i;
    for(i = first_empty - 1; i > FUNCTION_REGISTER; i--) {
        if(strcmp(symbol_table[i].name, name) == 0 
           && symbol_table[i].type == type)
            return i;
    }
    return -1;
}


char *get_name(int index) {
    if(index > -1 && index < SYMBOL_TABLE_LENGTH)
        return symbol_table[index].name;
    return "?";
}

unsigned get_kind(int index) {
    if(index > -1 && index < SYMBOL_TABLE_LENGTH)
        return symbol_table[index].kind;
    return NO_KIND;
}

unsigned get_type(int index) {
    if(index > -1 && index < SYMBOL_TABLE_LENGTH)
        return symbol_table[index].type;
    return NO_TYPE;
}

void set_attribute(int index, int attribute) {
    if(index > -1 && index < SYMBOL_TABLE_LENGTH)
        symbol_table[index].attribute = attribute;
}

unsigned get_attribute(int index) {
    if(index > -1 && index < SYMBOL_TABLE_LENGTH)
        return symbol_table[index].attribute;
    return NO_ATTRIBUTE;
}

void set_param_type(int index, unsigned number, unsigned type) {
    if(index > -1 && index < SYMBOL_TABLE_LENGTH) {
        if(symbol_table[index].param_types == 0) {
            symbol_table[index].param_types = 
                malloc(sizeof(unsigned) * PARAM_NUMBER);
            int i;
            for(i = 0; i < PARAM_NUMBER; i++)
                symbol_table[index].param_types[i] = NO_TYPE;
        }
        if(number > 0 && number <= PARAM_NUMBER)
            symbol_table[index].param_types[number - 1] = type;
    }
}

unsigned get_param_type(int index, unsigned number) {
    if(index > -1 && index < SYMBOL_TABLE_LENGTH)
        if(symbol_table[index].param_types && number > 0 
           && number <= PARAM_NUMBER)
            return symbol_table[index].param_types[number - 1];
    return NO_TYPE;
}

void set_register_type(int register_index, unsigned type) {
    if(register_index >= 0 && register_index <= FUNCTION_REGISTER)
        symbol_table[register_index].type = type;
}

// Brise elemente tabele simbola koji se nalaze posle proskledjenog indeksa.
void clear_symbols(unsigned begin_index) {
    int i;
    if(begin_index < 0)
        return;
    for(i = begin_index; i < first_empty; i++) {
        if(symbol_table[i].name)
            free(symbol_table[i].name);
        symbol_table[i].name = 0;
        symbol_table[i].kind = NO_KIND;
        symbol_table[i].type = NO_TYPE;
        symbol_table[i].attribute = NO_ATTRIBUTE;
        if(symbol_table[i].param_types)
            free(symbol_table[i].param_types);
        symbol_table[i].param_types = 0;
    }
    first_empty = begin_index;
}

// Brise sve elemente tabele simbola.
void clear_symtab(void) {
    first_empty = SYMBOL_TABLE_LENGTH;
    clear_symbols(0);
}

// Ispisuje sve elemente tabele simbola.
void print_symtab(void) {
    int i,j;
    printf("\n\nSYMBOL TABLE\n");
    printf("\n         name             kind       type attr p1 p2 p3 p4 p5");
    printf("\n-- ---------------- ---------------- ---- ---- -- -- -- -- --");
    for(i = 0; i < first_empty; i++) {
        printf("\n%2d %-16s %16s %4d %4d ", i,
               symbol_table[i].name, 
               symbol_kinds[(int)(logarithm2(symbol_table[i].kind))], 
               symbol_table[i].type, 
               symbol_table[i].attribute);
        if(symbol_table[i].param_types) {
            for(j = 0; j < PARAM_NUMBER; j++)
                printf("%2d ", symbol_table[i].param_types[j]);
        }
        else
            printf(" -");
    }
    printf("\n\n");
}

unsigned logarithm2(unsigned value) {
    unsigned mask = 1;
    int i = 0;
    for(i = 0; i < 32; i++) {
        if(value & mask)
            return i;
        mask <<= 1;
    }
    return 0; // ovo ne bi smelo da se desi; indeksiraj string "NONE"
}

// Inicijalizacija tabele simbola.
void init_symtab(void) {
    clear_symtab();

    insert_symbol(strdup("%0"),  WORKING_REGISTER, NO_TYPE);
    insert_symbol(strdup("%1"),  WORKING_REGISTER, NO_TYPE);
    insert_symbol(strdup("%2"),  WORKING_REGISTER, NO_TYPE);
    insert_symbol(strdup("%3"),  WORKING_REGISTER, NO_TYPE);
    insert_symbol(strdup("%4"),  WORKING_REGISTER, NO_TYPE);
    insert_symbol(strdup("%5"),  WORKING_REGISTER, NO_TYPE);
    insert_symbol(strdup("%6"),  WORKING_REGISTER, NO_TYPE);
    insert_symbol(strdup("%7"),  WORKING_REGISTER, NO_TYPE);
    insert_symbol(strdup("%8"),  WORKING_REGISTER, NO_TYPE);
    insert_symbol(strdup("%9"),  WORKING_REGISTER, NO_TYPE);
    insert_symbol(strdup("%10"), WORKING_REGISTER, NO_TYPE);
    insert_symbol(strdup("%11"), WORKING_REGISTER, NO_TYPE);
    insert_symbol(strdup("%12"), WORKING_REGISTER, NO_TYPE);
    insert_symbol(strdup("%13"), WORKING_REGISTER, NO_TYPE);
}

