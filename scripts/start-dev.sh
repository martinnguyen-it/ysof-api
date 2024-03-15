#!/bin/bash

echo "Script executed from: ${PWD}"
cd $0
source .venv/bin/activate
uvicorn app.main:app --reload
