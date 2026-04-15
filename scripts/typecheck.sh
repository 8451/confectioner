#!/bin/bash

cd "$(dirname "$0")/.."
uv run --active --no-sync --group dev mypy src/ tests/
