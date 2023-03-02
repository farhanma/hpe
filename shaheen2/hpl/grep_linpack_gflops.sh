#!/bin/bash

for i in `ls linpack-*nid*.out`
do
    grep "NODE ID" $i | awk '{print $3}' | tr '\n' ' '
    grep -A 3 "Performance Summary" $i | tail -n 1 | awk '{print $4}' | tr '\n' ' '
    echo
done
