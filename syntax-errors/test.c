
unsigned y() {
  return 2u;
}

int f(int p) {
  return p + p;
}

int main() {
  int a;
  a=0;

  if(a < 5u)  //?err
    a = 0;

  if(a  5)  //err
    return a;
  else a = 9;

  return a + 3 //err
}
