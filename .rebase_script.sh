#!/bin/bash
# Script to automatically set up rebase todo list
# First commit: pick, rest to squash: squash

sed -i.bak '1s/^pick/squash/; 2,7s/^pick/squash/' "$1"
rm -f "$1.bak"

