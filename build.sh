#!/bin/bash

if [ -d "src" ]; then
  echo "Running pylint on all Python files within src..."

  find "src" -type f -name "*.py" | while read -r file; do
    echo "Linting $file..."
    pylint "$file"
  done

  echo "Pylint checks completed."

  exit 0
else
  echo "src does not exist. Nothing to be done."

  exit 2
fi
