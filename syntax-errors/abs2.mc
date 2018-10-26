int abs(int i) {
  if(i < 0)
    return 0 - i;
  else 
    return i   //error
}

int main() {
  int x;
  x = -5       //error
  return abs(x);
}
