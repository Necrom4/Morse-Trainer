#!/usr/bin/env sh

rm -rf env
python3 -m venv env
source env/bin/activate
pip install -r requirements.txt
