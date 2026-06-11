#!/bin/bash
# set -e

# FOLDERS="qa stg"
FOLDERS="qa"
for FOLDER in $FOLDERS; do
    while read BUCKET; do

        # from emea-root
        echo "Giving full permission to bucket owner: $BUCKET/$FOLDER/"
        aws s3 --profile emea-root cp --storage-class STANDARD \
            --acl bucket-owner-full-control \
            --recursive \
            s3://$BUCKET/$FOLDER/ \
            s3://$BUCKET/$FOLDER/

        # from devops
        # echo "Giving full permission to bucket owner: $BUCKET/$FOLDER/"
        # aws s3 cp --storage-class STANDARD \
        #     --acl bucket-owner-full-control \
        #     --recursive \
        #     s3://$BUCKET/$FOLDER/ \
        #     s3://$BUCKET/$FOLDER/

        # echo "Changing ownership to emea-live: $BUCKET/$FOLDER/"
        # aws --profile emea-live s3 cp \
        #     --metadata-directive REPLACE \
        #     --recursive \
        #     s3://$BUCKET/$FOLDER/ \
        #     s3://$BUCKET/$FOLDER/
    done < <(cat buckets.txt)
done

# FOLDERS="dev"
# for FOLDER in $FOLDERS; do
#     while read BUCKET; do
#         echo "Giving full permission to bucket owner: $BUCKET/$FOLDER/"

#         aws s3 cp --storage-class STANDARD \
#             --acl bucket-owner-full-control \
#             --recursive \
#             s3://$BUCKET/$FOLDER/ \
#             s3://$BUCKET/$FOLDER/

#         echo "Changing ownership to bucket owner: $BUCKET/$FOLDER/"
#         aws --profile emea-live s3 cp \
#             --metadata-directive REPLACE \
#             --recursive \
#             s3://$BUCKET/$FOLDER/ \
#             s3://$BUCKET/$FOLDER/
#     done < <(cat buckets.txt)
# done

echo "DONE!"