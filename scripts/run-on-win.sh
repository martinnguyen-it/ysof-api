#!/bin/bash

echo "Script executed from: ${PWD}"
cd $0
.venv\Scripts\activate
uvicorn app.main:app --reload
