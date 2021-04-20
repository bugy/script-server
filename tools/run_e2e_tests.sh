#!/bin/bash

set -e

mkdir -p conf/runners
cp samples/configs/* conf/runners/

./launcher.py > /dev/null &
SERVER_PID=$!

set +e

cd src/e2e_tests

../../e2e_venv/bin/python -m pytest --alluredir /tmp/allure_result
STATUS=$?

kill $SERVER_PID
rm -rf conf/runners

allure generate /tmp/allure_result --clean -o /tmp/allure_report

exit $STATUS