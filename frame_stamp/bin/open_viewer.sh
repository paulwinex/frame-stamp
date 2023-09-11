#!/usr/bin/env bash


PYPATH=$(readlink -f "$(dirname $( readlink -f "${BASH_SOURCE:-$0}"))"/..)
export PYTHONPATH="$(dirname $PYPATH)"
python3 $PYPATH/viewer/dialog.py
