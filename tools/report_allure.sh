#!/bin/bash

aws s3 sync /tmp/allure_report "s3://script-server-tests/$TRAVIS_BRANCH/$TRAVIS_BUILD_NUMBER"
