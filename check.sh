#!/bin/bash
set -e

sudo pip install -r test-requirements.txt

pep8 servicelab/stack.py
pep8 servicelab/commands/*.py
