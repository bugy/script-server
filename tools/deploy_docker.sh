#!/usr/bin/env bash

set -e

if [ -z "$DOCKER_USER" ] || [ -z "$DOCKER_PASSWORD" ] || [ -z "$TRAVIS_BRANCH" ]; then
  echo 'Some environment variables are not set'
  exit -1
fi

IMAGE_NAME='bugy/script-server'

unzip -o build/script-server.zip -d build/script-server

if [ "$TRAVIS_BRANCH" == "stable" ]; then
  DOCKER_TAG='latest'
elif [ "$TRAVIS_BRANCH" == "master" ]; then
  DOCKER_TAG='dev'
else
  DOCKER_TAG="$TRAVIS_BRANCH"
fi

docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

docker login -u "$DOCKER_USER" -p "$DOCKER_PASSWORD"

docker buildx build --platform linux/amd64,linux/arm64 -f tools/Dockerfile -t "$IMAGE_NAME":"$DOCKER_TAG" .

echo "NEW_GIT_TAG=$NEW_GIT_TAG"
if [ ! -z "$NEW_GIT_TAG" ]; then
  docker tag "$IMAGE_NAME":"$DOCKER_TAG" "$IMAGE_NAME":"$NEW_GIT_TAG"
fi

docker push --all-tags "$IMAGE_NAME"
