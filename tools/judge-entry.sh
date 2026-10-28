#!/bin/bash
set -eu
. ~judge/.profile
export HOME=/tmp
exec /env/bin/dmoj-cli -c /config.yml --history /tmp/history --no-ansi "$@"
