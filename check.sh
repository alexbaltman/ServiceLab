#!/bin/bash
set -e

sudo pip install -r requirements.txt
sudo pip install -r test-requirements.txt

pep8 --max-line=93 servicelab/stack.py
pep8 --max-line=93 servicelab/commands/*.py
pep8 --max-line=93 servicelab/utils/*.py
pep8 --max-line=93 tests/*.py
python -m unittest discover .
