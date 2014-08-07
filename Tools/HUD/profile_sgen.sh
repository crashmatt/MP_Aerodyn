#!/bin/sh

python -m cProfile -o sgenprofile.txt soundgen.py
runsnake sgenprofile.txt

