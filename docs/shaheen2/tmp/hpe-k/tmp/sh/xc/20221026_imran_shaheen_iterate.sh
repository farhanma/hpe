#!/bin/bash

clear
for i in `seq 1 10000`
do
  clear
  echo "iteration #$i"
  echo
  date
  echo
  sinfo -R
  echo
  echo
  sinfo | grep idle
  echo
  sleep 180
  echo
done
