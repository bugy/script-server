#!/usr/bin/env bash

if [ -z "$TRAVIS_BRANCH" ] || [ -z "$OWNER" ] || [ -z "$GITHUB_TOKEN" ] || [ -z "$TRAVIS_REPO_SLUG" ]; then
    echo 'Some environment variables are not set'
    exit -1
fi

if [ "$TRAVIS_BRANCH" == "master" ]; then
    export NEW_GIT_TAG='dev'
    git tag -d 'dev'
    git push --delete origin 'dev'

elif [ "$TRAVIS_BRANCH" == "stable" ]; then
    version=`unzip -qc build/script-server.zip version.txt`
    export NEW_GIT_TAG="$version"
fi

set -e

if [ -z "$NEW_GIT_TAG" ]; then
    echo 'Skipping tagging of branch' "$TRAVIS_BRANCH"

else
    git config --local user.name 'bugy';
    git config --local user.email 'buggygm@gmail.com';
    git tag -f "$NEW_GIT_TAG";
    git remote add gh https://${OWNER}:${GITHUB_TOKEN}@github.com/${TRAVIS_REPO_SLUG}.git;
    git push -f gh "$NEW_GIT_TAG";
    git remote remove gh;
fi
