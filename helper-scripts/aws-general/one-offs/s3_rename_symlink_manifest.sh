#!/bin/bash

# replace content of files in s3_inventories

SOURCE_PATH="s3://ann01-tioprod-s3bucket-inventory/s3_inventories"
BUCKETS=$(aws s3 ls ${SOURCE_PATH}/ | awk '{print $2}' | cut -f1 -d'/')

#BUCKETS="annalect-annalect-audiencebuilder"

for bucket in $BUCKETS; do

SOURCE_PATH="s3://ann01-tioprod-s3bucket-inventory/s3_inventories/${bucket}/inventory/hive"
FOLDERS=$(aws s3 ls ${SOURCE_PATH}/ | awk '{print $2}' | grep "/$")
FILENAME="symlink.txt"


    # ONLY_FOLDER="dt=2020-05-06-00-00"

    for folder in $FOLDERS; do

        if [ ! -z "${ONLY_FOLDER}" ] && [ "$folder" != "${ONLY_FOLDER}/" ]; then
            #echo "Not the wanted folder ${ONLY_FOLDER} ($folder) "
            continue
        fi

        aws s3 cp --quiet ${SOURCE_PATH}/${folder}${FILENAME} /tmp
        if grep -q "annalecttio/data" /tmp/${FILENAME}; then
            echo "Found in ${SOURCE_PATH}/${folder}${FILENAME}"

            #echo "annalecttio?"
            #cat /tmp/${FILENAME} | grep "annalecttio\/data"
            #cat /tmp/${FILENAME} | grep "s3://ann01-tioprod-s3bucket-inventory"

            sed -i -r 's/annalecttio\/data/inventory\/data/g' /tmp/${FILENAME}
            sed -i -r 's#s3://annalect-s3-analytics#s3://ann01-tioprod-s3bucket-inventory#g' /tmp/${FILENAME}

            #echo "inventory?"
            #cat /tmp/${FILENAME} | grep "inventory\/data"
            #cat /tmp/${FILENAME} | grep "s3://ann01-tioprod-s3bucket-inventory"
            #exit 1

            aws s3 cp --quiet /tmp/${FILENAME} ${SOURCE_PATH}/${folder}${FILENAME}
            rm /tmp/${FILENAME}
            continue
        fi
        #echo "Not found in $folder"

    done
done

for bucket in $BUCKETS; do

SOURCE_PATH="s3://ann01-tioprod-s3bucket-inventory/s3_inventories/${bucket}/inventory"
FOLDERS=$(aws s3 ls ${SOURCE_PATH}/ | awk '{print $2}' | grep "/$")
FILENAME="manifest.json"

    #ONLY_FOLDER="2020-05-06T00-00Z"

    for folder in $FOLDERS; do

        if [ ! -z "${ONLY_FOLDER}" ] && [ "$folder" != "${ONLY_FOLDER}/" ]; then
            #echo "Not the wanted folder ${ONLY_FOLDER} ($folder) "
            continue
        fi

        aws s3 cp --quiet ${SOURCE_PATH}/${folder}${FILENAME} /tmp
        if grep -q "annalecttio/data" /tmp/${FILENAME}; then
            echo "Found in ${SOURCE_PATH}/${folder}${FILENAME}"

            #echo "annalecttio?"
            #cat /tmp/${FILENAME} | grep "annalecttio\/data"
            #cat /tmp/${FILENAME} | grep "s3://ann01-tioprod-s3bucket-inventory"

            sed -i -r 's/annalecttio\/data/inventory\/data/g' /tmp/${FILENAME}
            #sed -i -r 's#s3://annalect-s3-analytics#s3://ann01-tioprod-s3bucket-inventory#g' /tmp/${FILENAME}

            #echo "inventory?"
            #cat /tmp/${FILENAME} | grep "inventory\/data"
            #cat /tmp/${FILENAME} | grep "s3://ann01-tioprod-s3bucket-inventory"

            # exit 1

            aws s3 cp --quiet /tmp/${FILENAME} ${SOURCE_PATH}/${folder}${FILENAME}
            rm /tmp/${FILENAME}
            continue
        fi
        #echo "Not found in $folder"

    done
done

echo FIN

