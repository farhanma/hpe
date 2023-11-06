#!/bin/sh

ip_address='127.0.0.1'
ip_port='9965'

networksetup -setsocksfirewallproxystate Wi-Fi on
networksetup -setsocksfirewallproxy Wi-Fi $ip_address $ip_port

ssh -D $ip_port -C -N farhanma@ilogin.ibex.kaust.edu.sa
