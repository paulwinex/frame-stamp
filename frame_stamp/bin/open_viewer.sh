#!/usr/bin/env bash

# activate virtual env before start
PYPATH=$(readlink -f "$(dirname $( readlink -f "${BASH_SOURCE:-$0}"))"/../..)
export PYTHONPATH=$PYPATH
cd ../viewer
python3 dialog.py
