#!/usr/bin/env bash
# exit on error
set -o errexit

# Upgrade pip and setuptools to ensure wheel compatibility
python -m pip install --upgrade pip setuptools wheel

# Install dependencies from requirements.txt
# We use --only-binary :all: for heavy packages to avoid compiling from source
python -m pip install -r requirements.txt
