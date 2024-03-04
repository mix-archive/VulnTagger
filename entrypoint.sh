#!/bin/bash

set -e

if [ -z "$FLAG" ]; then
    echo "FLAG is not set"
    export FLAG="flag{test}"
fi

echo -n $FLAG > /flag
unset FLAG
chown bot:bot /flag
chmod 400 /flag

su app -c 'python -m vulntagger' &
su bot -c 'python /app/bot.py'

# Kill all processes
kill -9 -1