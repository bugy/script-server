#!/usr/bin/env bash

if [ -z "$TRAVIS_BRANCH" ] || [ -z "$OWNER" ] || [ -z "$GITHUB_TOKEN" ] || [ -z "$TRAVIS_REPO_SLUG" ]; then
    echo 'Some environment variables are not set'
    exit -1
fi

if [ "$TRAVIS_BRANCH" == "master" ]; then
    export NEW_GIT_TAG='dev'

elif [ "$TRAVIS_BRANCH" == "stable" ]; then
    last_tag=`git describe --abbrev=0 --tags`
    npm_tag=`grep -Po '"version": "\d+.\d+.\d+"' web-src/package.json | grep -Po '\d+.\d+.\d+'`
    minor_npm_version=${npm_tag%.*}
    if [ ${last_tag%.*} == "$minor_npm_version" ]; then
        patch_npm_version=${npm_tag##*.}
        next_patch_version=$((patch_npm_version + 1))
        export NEW_GIT_TAG="$minor_npm_version.$next_patch_version"
    else
        export NEW_GIT_TAG="$npm_tag"
    fi
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
