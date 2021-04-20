#!/bin/bash

set -e

mkdir conf/runners
cp samples/configs/* conf/runners/

./launcher.py &
SERVER_PID=$!

set +e

cd src/e2e_tests

../../e2e_venv/bin/python -m pytest
STATUS=$?

kill $SERVER_PID
rm -rf conf/runners

exit $STATUS