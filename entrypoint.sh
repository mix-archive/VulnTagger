#!/bin/bash

set -e

if [ -z "$FLAG" ]; then
    echo "FLAG is not set"
    export FLAG="flag{test}"
fi

echo -n $FLAG > /flag
unset FLAG

su app -c 'python -m vulntagger' &
su app -c 'python /app/bot.py'

# Kill all processes
kill -9 -1