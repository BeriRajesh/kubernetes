#!/bin/bash
HOST="10.5.230.250"
DB="empowerid"
USER="aok.reporting"
SCRIPT=/home/bamboo/devops/empowerid-quries/apple-vs-google-access.sql
OUTPUT=/home/bamboo/devops/empowerid-quries/apple-vs-google-access.csv
LOGFILE=/home/bamboo/logs/apple-vs-google-access.log
#EMAIL="shashikant.kuwar@annalect.com Konstantin.Markov@annalect.com"
EMAIL="Michele.Pirri@annalect.com Melitta.Ellerbe@annalect.com Christina.Xing@annalect.com  Konstantin.Markov@annalect.com"
MSG="PFA Report"

key_id='alias/secrets'
ciphertext_blob_path=/home/bamboo/.credentials

passphrase=$(/usr/local/bin/aws --region us-east-1 kms decrypt  --ciphertext-blob fileb://$ciphertext_blob_path/$USER --query Plaintext --output text | base64 --decode) || exit 1

echo "PFA Validation Report" > /home/bamboo/logs/msg.txt
if [  -f $OUTPUT ];then
mutt  -e "set content_type=text/html" -s "Validation Report for Apple Access versus Google" < /home/bamboo/logs/msg.txt -a "$OUTPUT" -- $EMAIL || exit 1
fi
#END
