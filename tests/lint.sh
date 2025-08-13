#!/bin/bash

set -e

echo "--- Lint Check Begin ---"

black --check .

echo "Lint Check PASSED"