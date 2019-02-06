#!/usr/bin/env bash

set -e

if [ -z "$DOCKER_USER" ] || [ -z "$DOCKER_PASSWORD" ] || [ -z "$TRAVIS_BRANCH" ] || [ -z "$COMMIT" ]; then
    echo 'Some environment variables are not set'
    exit -1
fi

IMAGE_NAME='bugy/script-server'

unzip -o build/script-server.zip -d build/script-server

docker build -f tools/Dockerfile -t "$IMAGE_NAME":"$COMMIT" .

docker login -u "$DOCKER_USER" -p "$DOCKER_PASSWORD"

if [ "$TRAVIS_BRANCH" == "stable" ]; then
    docker tag "$IMAGE_NAME":"$COMMIT" "$IMAGE_NAME":latest
elif [ "$TRAVIS_BRANCH" == "master" ]; then
    docker tag "$IMAGE_NAME":"$COMMIT" "$IMAGE_NAME":dev
else
    docker tag "$IMAGE_NAME":"$COMMIT" "$IMAGE_NAME":"$TRAVIS_BRANCH"
fi

docker push "$IMAGE_NAME"