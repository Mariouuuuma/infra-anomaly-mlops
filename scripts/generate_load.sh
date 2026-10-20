#!/usr/bin/env bash
# Light random activity so "normal" is not a flat line.
# Run it from the project folder (it uses vagrant ssh).
while true; do
  for i in $(seq 1 $((RANDOM % 30 + 5))); do
    curl -s -o /dev/null http://192.168.56.11/
  done
  if [ $((RANDOM % 10)) -eq 0 ]; then
    vagrant ssh web01 -c "stress-ng --cpu 1 --cpu-load 30 --timeout 30s" >/dev/null 2>&1
  fi
  sleep $((RANDOM % 60 + 20))
done
