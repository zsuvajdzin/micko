

#include <stdlib.h>
#include <stdio.h>
#include "stack.h"

// sp se krece od vecih ka manjim indeksima
// sp pokazuje na poslednju popunjenu lokaciju

void push(stack *s, int val) {
    if(s->sp == 0) {
        printf("\nCompiler error! Stack overflow!\n");
        exit(EXIT_FAILURE);
    }
    s->values[--s->sp] = val;
}

int pop(stack *s) {
    if(s->sp >= STACK_SIZE) {
        printf("\nCompiler error! Stack underflow!\n");
        exit(EXIT_FAILURE);
    }
    return s->values[s->sp++];
}

int top(stack *s) {
    if(s->sp >= STACK_SIZE) {
        printf("\nCompiler error! Stack underflow!\n");
        exit(EXIT_FAILURE);
    }
    return s->values[s->sp];
}

void init_stack(stack *s) {
    s->sp = STACK_SIZE;
}
