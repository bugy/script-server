#!/bin/bash

echo $@

my_file=''

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -f)
    my_file="$2"
    shift # past argument
    shift # past value
    ;;
    *)    # unknown option
    POSITIONAL+=("$1") # save it in an array for later
    shift # past argument
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

echo
if [ -z "$my_file" ]; then
    echo '-f is empty'
else
    echo '-f content:'
    cat "$my_file"
fi
