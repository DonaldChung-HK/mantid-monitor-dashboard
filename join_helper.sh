#!/bin/bash
# A bash script to reconstruct JSON and remove splitted files in directory

function join_file_and_delete() {
    DIR_NAME=$(basename "$1")
    ORIG_FILENAME=${DIR_NAME:0:-14} #this is to remove the --bashsplitted folder suffix
    cd $1
    cat *.jsonsplit > $ORIG_FILENAME
    mv $ORIG_FILENAME ../
    cd ..
    rm -r $DIR_NAME
}

export -f join_file_and_delete
find . -name "*--bashsplitted" -exec bash -c "join_file_and_delete \"{}\"" \;