#!/bin/bash

if [ -d "output" ]; then
  echo "Cleaning output..."
  rm -rf output
  echo "Output cleaned."
else
  echo "Nothing to clean."
fi

mkdir output

exit 0
