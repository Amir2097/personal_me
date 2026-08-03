#!/bin/sh
set -e

cd /app

needs_install() {
  [ ! -d node_modules ] || [ ! -f node_modules/.package-lock.json ] || [ package-lock.json -nt node_modules/.package-lock.json ]
}

install_deps() {
  echo "Installing billiards npm dependencies..."
  # Use npm install (not ci) so lockfile drift from host/node versions does not crash the container.
  npm install --loglevel=warn
}

if needs_install; then
  attempt=1
  max_attempts=5
  while [ "$attempt" -le "$max_attempts" ]; do
    if install_deps; then
      break
    fi
    if [ "$attempt" -eq "$max_attempts" ]; then
      echo "npm install failed after ${max_attempts} attempts."
      exit 1
    fi
    echo "Attempt ${attempt} failed, retrying in $((attempt * 5))s..."
    sleep $((attempt * 5))
    attempt=$((attempt + 1))
  done
fi

echo "Preparing Nuxt for billiards..."
rm -rf node_modules/.cache/vite
npx nuxt prepare

exec "$@"
