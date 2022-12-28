#!/bin/bash
# A bash script to split and remove JSON file that is too big change the FILE_SIZE_LIMIT to suit your need

FILE_SIZE_LIMIT=90 # in MB


function split_file_and_delete() {
    FILE_NAME=$(basename "$2")
    DIR_Name=$(dirname "$2")
    cd $DIR_Name
    split -b $1MB --additional-suffix ".jsonsplit" $FILE_NAME $FILE_NAME 
    mkdir -p $FILE_NAME--bashsplitted
    mv $FILE_NAME*.jsonsplit $FILE_NAME--bashsplitted
    rm $FILE_NAME
}

export -f split_file_and_delete
find . -size +"$FILE_SIZE_LIMIT"M -name "*.json" -exec bash -c "split_file_and_delete $FILE_SIZE_LIMIT \"{}\"" \; # change the file size for different chunk size