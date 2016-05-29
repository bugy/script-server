#!/bin/bash

repeats=1
text="I'm called"

while (( $# >= 1 ))
do
key="$1"

case $key in
    -r)
    repeats="$2"
    echo "repeats = $repeats"
    shift # past argument
    ;;
    -t)
    text="$2"
    echo "text = $text"
    shift # past argument
    ;;
    --clear)
    echo "Clearing the file..."
    > ~/simple.txt
    ;;
    *)
    # unknown option
    ;;
esac
shift # past argument or value
done

read -p "Press enter to start writing to the file"

for (( i=0; i<repeats ; i++ ))
do
   echo "$text" >> ~/simple.txt
done

echo "File content >> \n"
cat ~/simple.txt
