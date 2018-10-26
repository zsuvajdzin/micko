
#ifndef SYMTAB_H
#define SYMTAB_H

#define PARAM_NUMBER   5

// Element tabele simbola
typedef struct sym_entry {
    char *name;               // ime simbola
    unsigned kind;            // vrsta simbola
    unsigned type;            // tip vrednosti simbola
    int attribute;            // dodatni attribut
    unsigned *param_types;    // tipovi parametara
} SYMBOL_ENTRY;

int  get_next_empty_element(void);
int  insert_symbol(char *name, unsigned kind, unsigned type);
int  try_to_insert_id(char *name, unsigned kind, unsigned type);
int  try_to_insert_constant(char *str, unsigned type);
int  lookup_symbol(char *name, unsigned kind);
int  lookup_constant(char *name, unsigned type);

char*    get_name(int index);
unsigned get_kind(int index);
unsigned get_type(int index);
void     set_attribute(int index, int attribute);
unsigned get_attribute(int index);
void     set_param_type(int index, unsigned number, unsigned type);
unsigned get_param_type(int index, unsigned number);
void     set_register_type(int register_index, unsigned type);

void     clear_symbols(unsigned begin_index);
void     clear_symtab(void);
void     print_symtab(void);
unsigned logarithm2(unsigned value);
void     init_symtab(void);

#endif
