#!/bin/bash

if [ -d "tests" ]; then
  echo "Running tests..."
  cd tests || exit 3
  pytest
  exit $?
else
  echo "tests dir doesn't exist. Nothing to do."

  exit 4
fi