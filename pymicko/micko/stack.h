
#ifndef STACK_H
#define STACK_H

#define STACK_SIZE    32

typedef struct int_stack {
    int sp;                            // stack pointer
    int values[STACK_SIZE];            // stack elements
} stack;


void push(stack *s, int val);
int  pop(stack *s);
int  top(stack *s);
void init_stack(stack *s);

#endif
