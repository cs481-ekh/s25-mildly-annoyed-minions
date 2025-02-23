#!/bin/bash

if [ -d "test" ]; then
  echo "Running tests..."
  cd test || exit 3
  pytest
  exit $?
else
  echo "test dir doesn't exist. Nothing to do."

  exit 4
fi