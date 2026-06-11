#!/bin/bash

# download *.gz from s3,  uncompress, upload to s3

DATE="2019/06/30"
PATHS3="annalect/acxiom/infobase/$DATE/"
SOURCES3="s3://omg-agencies/${PATHS3}"
DESTINATION="s3://annalect-acxiom-agileid/raw/audience/${DATE}"

echo -n "Synchronizing '$DATE'. Are you sure (y/N)? "
read ans
if [ ! "$ans" == "y" ]
then
    echo "Please update script and try again"
    exit 1
fi

echo
echo -ne "Files will be transferred preserving the same original folder structure:\n\n\tfrom\t$SOURCES3 \n\tto\t$DESTINATION \n\nDo you want to proceed (y/N)? "
read ans

if [ ! "$ans" == "y" ]
then
    echo "Please update script and try again"
    exit 1
fi


for l in $(aws s3 ls ${SOURCES3});
do
    if [[ $l =~ \.gz$ ]]
    then
        UNZIPPED_FNAME=${l%.gz}
        if [ $(aws s3 ls ${DESTINATION}${UNZIPPED_FNAME} | wc -l) -eq 0 ]
        then
            echo "Downloading ${l}"
            aws s3 cp ${SOURCES3}$l .
            echo "Uncompressing ..."
            gzip -d $l
            echo "Copying to ${DESTINATION}..."
            aws s3 cp ${l%.gz} ${DESTINATION}
            echo "Deleting "${UNZIPPED_FNAME}""
            rm "${UNZIPPED_FNAME}"
            echo
        else
            echo Already exists: ${DESTINATION}
        fi
        # exit 0
    fi
done
