#!/bin/bash
set -eu
. ~judge/.profile
export HOME=/tmp
if [ "${1:-}" = "--metadata" ]; then
    exec /env/bin/python3 /runtime-metadata.py
fi
exec /env/bin/dmoj-cli -c /config.yml --history /tmp/history --no-ansi \
    --only-executors CPP11,CPP14,CPP17,CPP20,CPP23 "$@"
