#!/usr/bin/env bash
# Perplexity MCPサーバーの起動スクリプト。
# APIキーは同じフォルダの .env から読み込む（キーを .mcp.json に書かないため）。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [ -f "$ROOT/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$ROOT/.env"
  set +a
fi

if [ -z "${PERPLEXITY_API_KEY:-}" ]; then
  echo "PERPLEXITY_API_KEY が設定されていません。.env.example をコピーして .env を作り、キーを設定してください。" >&2
  exit 1
fi

# -q: インストール時のメッセージを標準出力に出さない（MCPの通信を壊さないため）
exec npx -yq @perplexity-ai/mcp-server
