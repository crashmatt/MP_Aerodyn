#!/bin/sh

python -m cProfile -o hudprofile.txt mav_pihud.py --master=localhost:14550 --baudrate=115200 --target-system=55 --target-component=1 --source-system=251
runsnake hudprofile.txt

