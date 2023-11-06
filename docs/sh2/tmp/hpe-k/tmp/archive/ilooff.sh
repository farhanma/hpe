#!/bin/sh

ip_port='9965'

lsof -ti:$ip_port | xargs kill -9
networksetup -setsocksfirewallproxystate Wi-Fi off
