#!/usr/bin/env bash
# Quick check that .env exists before running the app.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ ! -f "${ROOT_DIR}/.env" ]]; then
  echo "Missing .env — copy .env.example to .env and fill in values."
  exit 1
fi

echo ".env found."
