#!/usr/bin/env bash

# activate virtual env before start
export PYTHONPATH="$(realpath $( dirname $( dirname "${BASH_SOURCE[0]}" )))"
source /mnt/toolbox/pipeline/cgf_libs/all/cgf_tools/env.sh
echo $PYTHONPATH
cd "$( dirname "${BASH_SOURCE[0]}" )"/viewer
python ./dialog.py
