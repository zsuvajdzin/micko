    int a;
    int b;
    int c;
    unsigned d;

    int fun1(int x, unsigned y) {
        return 123;
    }

    int fun2(int a) {
        return 1 + a * fun1(a, 456u);
    }

    int main(int x, int y) {
        int w;
        unsigned z;
        if (9 > 8 && 2 < 3 || 6 != 5 && a <= b && c < x || w >= y) {
            a = b + 1;
            if (x == y)
                while (d < 4u)
                    x = x * w;
            else
                while (a + b < c - y && x > 3 || y < 2)
                    if (z > d)
                        a = a - 4;
                    else
                        b = a * b * c * x / y;
        }
        else
            c = 4;
        a = fun1(x,d) + fun2(fun1(fun2(w + 3 * 2) + 2 * c, 2u));
        return 2;
    }

