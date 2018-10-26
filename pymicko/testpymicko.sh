#!/bin/bash

PY_OUT=outputpm.asm
YA_OUT=output.asm

rm $PY_OUT $YA_OUT
python pymicko.py $1 $PY_OUT
if [ $? -ne 0 ]; then
    exit
fi
./micko/a.out < $1
if [ $? -ne 0 ]; then
    exit
fi
diff $YA_OUT $PY_OUT 2>/dev/null 1>/dev/null
if [ $? -eq 0 ]; then
    echo "Generisani fajlovi su isti."
else
    kompare $YA_OUT $PY_OUT
fi

