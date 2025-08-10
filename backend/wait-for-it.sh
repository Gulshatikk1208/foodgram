#!/usr/bin/env bash

host="$1"
port="$2"
shift 2
cmd="$@"

until (echo > /dev/tcp/$host/$port) >/dev/null 2>&1; do
    sleep 1
done

exec $cmd