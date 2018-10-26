
#ifndef DEFS_H
#define DEFS_H

#define bool int
#define TRUE  1
#define FALSE 0

#define SYMBOL_TABLE_LENGTH 40

#define NO_ATTRIBUTE -1

//tipovi podataka (moze ih biti maksimalno 8)
enum { NO_TYPE, INT_TYPE, UNSIGNED_TYPE };

// vrste simbola (moze ih biti maksimalno 32)
enum { NO_KIND = 0x1, WORKING_REGISTER = 0x2, GLOBAL_VAR = 0x4,
       FUNCTION = 0x8, PARAMETER = 0x10, LOCAL_VAR = 0x20,
       CONSTANT = 0x40 };

static char *symbol_kinds[] = { "NONE", "WORKING_REGISTER", "GLOBAL_VAR",
                                "FUNCTION", "PARAMETER", "LOCAL_VAR",
                                "CONSTANT" };

//konstante arithmetickih operatora
enum { ADD_OP, SUB_OP, MUL_OP, DIV_OP };
//stringovi za ispis aritmetickih operatora
static char *arithmetic_operators[2][4] = { {"ADDS", "SUBS", "MULS", "DIVS"},
                                            {"ADDU", "SUBU", "MULU", "DIVU"} };

//konstante relacionih operatora
enum { LT, GT, LE, GE, EQ, NE, RELOP_NUMBER };
//konstante uslovnih skokova:
enum { LTS, GTS, LES, GES, EQS, NES,
       LTU, GTU, LEU, GEU, EQU, NEU };
//stringovi za ispis 'jump' naredbi
static char* jumps[]= { "JLTS", "JGTS", "JLES", "JGES", "JEQ ", "JNE ",
                        "JLTU", "JGTU", "JLEU", "JGEU", "JEQ ", "JNE " };
static char* opposite_jumps[]={"JGES", "JLES", "JGTS", "JLTS", "JNE ", "JEQ ",
                               "JGEU", "JLEU", "JGTU", "JLTU", "JNE ", "JEQ "};
//string za ispis 'JMP' naredbe
static char* unconditional_jump = "JMP ";

//stringovi za ispis 'CMP' naredbi
static char* cmps[] = { "CMPS", "CMPU" };

//konstante multiplikativnih operatora
enum { TIMES = 1, DIV };

//konstante nivoa opsega vazenja
enum { GLOBAL_LEVEL, LOCAL_LEVEL, PARAMETER_LEVEL };

#define LAST_WORKING_REGISTER    12
#define FUNCTION_REGISTER        13

#define TYPE_BIT_SIZE            16
#define CHAR_BUFFER_LENGTH       128

#endif

