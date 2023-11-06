#!/bin/bash

ssh crayadm@smw2
passowrd: mocixc40

/home/crayadm/bin/check_hsn

./bin/check_hsn | grep -A 2 -B 17 "17.0M"

xtchecklink -S | egrep 'c4-3c2s13a0l15|c0-2c2s13a0l14'

rtr --connector-link-map=c0-2c2s13a0l14
rtr --connector-link-map=c4-3c2s13a0l15

xtwarmswap --remove-cable c0-2c2j33
xtwarmswap --add-cable c0-2c2j33 --linktune
