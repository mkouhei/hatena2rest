#!/bin/sh

cd out
test -x $(which tinker) && tinker=$(which tinker)
$tinker -s
mv -f master.rst.tmp master.rst
$tinker -b -q