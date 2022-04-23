#!/bin/bash

set -o xtrace
set -e

if grep -E 'SwapTotal:\s+0+\s+kB' /proc/meminfo; then
    echo "Positively identified no swap space, creating some."
    fallocate -l 512G /swapfile
    chmod 600 /swapfile
    /sbin/mkswap /swapfile
    /sbin/swapon /swapfile
else
    echo "Did not confirm zero swap space, doing nothing."
fi