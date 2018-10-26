int a;
int b;
int c;
int d;
int e;

unsigned u;
unsigned w;

int f(int x) {
    return x + 2;
}

int f2(int z) {
    return z;
}

unsigned f3(unsigned z) {
    return z;
}

unsigned pi100() {
    return 628u;
}

int main(int argv) {
    int aa;
    int bb;
    int c;
    int d;
    unsigned uu;
    unsigned w;

    //poziv funkcije
    a = f(a + b);

    a = f(1);
    
    a = f(-1);
    
    u = f3(w);
    
    u = f3(5u);

    //if iskaz sa else delom
    if(a < b)
        a = 1;
    else
        a = -2;

    if(u < w)
        u = 1u;
    else
        w = 2u;

    if(a + c < b + d - 4)
        a = 1;
    else
        a = 2;

    //ugnjezdeni if iskazi
    if(a < b)
        if(u == w) {
            u = 1u;
            a = f(1);
        }
        else {
            w = 2u;
            u = f3(5u);
        }
    else {
        if(a + c == b + d - -4) {
            a = 1;
            if (a + aa < b + bb)
                uu = w-u+uu;
            else
                d = aa+bb-c;
        }
        else
            a = 2;
        a = f(a + b);
    }

    //if iskaz bez else dela
    if(a < b)
        a = 1;

    if(a + c == b - d - +4)
        a = 1;
}

