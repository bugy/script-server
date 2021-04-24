#!/bin/bash

aws s3 sync /tmp/allure_report "s3://script-server-tests/$TRAVIS_BRANCH/$TRAVIS_BUILD_NUMBER"

allure_url="https://script-server-tests.s3-us-west-2.amazonaws.com/$TRAVIS_BRANCH/$TRAVIS_BUILD_NUMBER/index.html"
echo "Test results: $allure_url"

if [ "$TRAVIS_PULL_REQUEST" != "false" ]; then
  curl -H "Authorization: token ${GITHUB_TOKEN}" -X POST \
    -d "{\"body\": \"Test results: $allure_url\"}" \
    "https://api.github.com/repos/${TRAVIS_REPO_SLUG}/issues/${TRAVIS_PULL_REQUEST}/comments"
fi
