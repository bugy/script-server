#!/bin/bash

args=("$@")
echo $@

my_file=''
recurs_file=''

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    --file_upload)
    my_file="$2"
    shift # past argument
    shift # past value
    ;;
    --recurs_file)
    recurs_file="$2"
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
echo 'Arguments:'
printf '%s\n' "${args[@]}"

echo

if [ ! -z "$recurs_file" ]; then
    echo "recurs_file=$recurs_file"
    echo "md5="`md5sum "$recurs_file"`
fi

echo

if [ -z "$my_file" ]; then
    echo '--file_upload is empty'
else
    echo '--file_upload content:'
    cat "$my_file"
fi

sleep 5