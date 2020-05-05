#!/usr/bin/env bash

# activate virtual env before start
export PYTHONPATH="$(realpath $( dirname $( dirname $( dirname "${BASH_SOURCE[0]}" ))))"
source /mnt/toolbox/pipeline/cgf_libs/all/cgf_tools/env.sh
cd "$( dirname $( dirname "${BASH_SOURCE[0]}" ))"/viewer
python3 ./dialog.py
