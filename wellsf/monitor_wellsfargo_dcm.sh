#!/bin/bash
YESTERDAY=$(date -d "1 day ago" '+%Y%m%d')
YESTERDAY_DASH=$(date -d "1 day ago" '+%Y-%m-%d')
DATED=${1:-$YESTERDAY}
DATED_DASH=${2:-$YESTERDAY_DASH}
SHORTDATE=$(date +%Y%m%d-%H%M)
gcp_files="check_files_dcm/gcp_files_${SHORTDATE}.txt"
sftp_files="check_files_dcm/sftp_files_${SHORTDATE}.txt"
missing_files="check_files_dcm/missing_files_${SHORTDATE}.txt"
to_day=$(date '+%A')
DATE=$(date +%Y-%m-%d)
DAILY_CHECK_FILE="/home/xferuser/check_files_dcm/$(date +%Y%m%d)-files-OK"

#scriptname=$(basename -- $0)
#processes=$(pgrep -lf ${scriptname} | grep -v vim | wc -l)
#pgrep -lf ${scriptname} | grep -v vim
#echo $?
#echo "-$processes-"
#if [ "${processes:-0}" -gt "1" ]; then
#    # theres more than one process
#    echo "${scriptname} already running"
#    exit 1
#fi
#exit 0
# check if files have already been uploaded to sftp
echo "Check existence of file: ${DAILY_CHECK_FILE}"
if [ -f "$DAILY_CHECK_FILE" ]
then
    echo "Date: ${DATE}. Files already validated and uploaded."
    exit 0
fi

echo "WellsFargo-DS3 (DoubleClickSearch)Missing Files -"$DATED"-" >  $missing_files
echo "----------------------------------------------------------" >> $missing_files
echo Report_Dated: $DATED
cat /dev/null > "$gcp_files"

# function to verify if there are the right number of files in the SFTP
#   if there are not the right number of files, and if its later than 23h, it sends an alert by email
function validate_wf () {
    echo "validating..."
    num_missing_files=$(cat $missing_files | grep "<" | wc -l)
    num_sftp_files=$(cat ${sftp_files} | sort | uniq | wc -l)
    echo "Num missing files: ${num_missing_files}"
    if  [ "${num_missing_files}" -ne 0 ]; then
        # only send email if hour > 23h
        if [ "$(date +%H)" -ge "23" ]
            then
            echo "" >> $missing_files
            echo "" >> $missing_files
            echo "TIP: You should be able to trigger a manual run remotely by running " >> $missing_files
            echo "    sshg 10.5.231.240 'sudo --user xferuser -- /home/xferuser/wells_fargo/ds3/MANUAL_RUN_daemon-ds3.py -d YYYY-MM-DD -q keyword|conversion|visit [ -q keyword|conversion|visit -q ... ]''" >> $missing_files
            echo "n.b. (the script activates automatically the virtualenvironment)" >> $missing_files
            echo "n.b2 this script could sync ALL files executing " >> $missing_files
            echo "    /home/xferuser/wells_fargo/ds3/MANUAL_RUN_daemon-ds3.py -d $DATED_DASH -q keyword -q conversion -q visit " >> $missing_files
            echo "" >> $missing_files
            echo "(and finally we could also change the cron to execute this monitor after 15:00 every hour)" >> $missing_files

            cat $missing_files | mail -s "(MustSee)Wells Fargo :: C2T:-Missing DCM file <"$DATED">"  adt@annalect.cloud
            return 1
            exit 1
        fi
    elif  [ "${num_missing_files}" -eq 0 ]; then
        echo "Files present in SFTP. All OK."
        echo "$(cat ${sftp_files})" >> $DAILY_CHECK_FILE
        exit 0
    fi
}

# list of files that need to be uploaded to sftp
dcm_files="activity_$DATED.ctl
activity_$DATED.txt.gz
activity_cats_$DATED.ctl
activity_cats_$DATED.txt.gz
activity_types_$DATED.ctl
activity_types_$DATED.txt.gz
ad_placement_assignments_$DATED.ctl
ad_placement_assignments_$DATED.txt.gz
ads_$DATED.ctl
ads_$DATED.txt.gz
advertisers_$DATED.ctl
advertisers_$DATED.txt.gz
browsers_$DATED.ctl
browsers_$DATED.txt.gz
campaigns_$DATED.ctl
campaigns_$DATED.txt.gz
cities_$DATED.ctl
cities_$DATED.txt.gz
click_$DATED.ctl
click_$DATED.txt.gz
conversion_$DATED.ctl
conversion_$DATED.txt
creative_ad_assignments_$DATED.ctl
creative_ad_assignments_$DATED.txt.gz
creatives_$DATED.ctl
creatives_$DATED.txt.gz
custom_creative_fields_$DATED.ctl
custom_creative_fields_$DATED.txt.gz
custom_floodlight_variables_$DATED.ctl
custom_floodlight_variables_$DATED.txt.gz
custom_rich_media_$DATED.ctl
custom_rich_media_$DATED.txt.gz
designated_market_areas_$DATED.ctl
designated_market_areas_$DATED.txt.gz
impression_$DATED.ctl
impression_$DATED.txt.gz
keyword_$DATED.ctl
keyword_$DATED.txt
keyword_value_$DATED.ctl
keyword_value_$DATED.txt.gz
operating_systems_$DATED.ctl
operating_systems_$DATED.txt.gz
paid_search_$DATED.ctl
paid_search_$DATED.txt.gz
placement_cost_$DATED.ctl
placement_cost_$DATED.txt.gz
placements_$DATED.ctl
placements_$DATED.txt.gz
sites_$DATED.ctl
sites_$DATED.txt.gz
states_$DATED.ctl
states_$DATED.txt.gz
visit_$DATED.ctl
visit_$DATED.txt"

for file in "${dcm_files[@]}"; do
    echo -e "$file" >> "$gcp_files"
done

# logs files present in sftp
echo ls | sftp wf-prod:/'$$ id=325114' | sort | uniq | grep "$DATED". > "${sftp_files}"

# logs missing files in sftp
diff -Z "$gcp_files" "$sftp_files" |  grep "<" >> "$missing_files"
diff -Z "$gcp_files" "$sftp_files" |  grep "<"

# check if the correct number of files are present in sftp
#   send email alert if later than 23h
validate_wf
echo "Trying to upload files again..."
exit 1
# if necessary try to upload all files of type keyword/conversion/visit
if grep -q -P "(keyword|conversion|visit)_" $missing_files
then
    /home/xferuser/wells_fargo/ds3/MANUAL_RUN_daemon-ds3.py -d ${DATE} -q keyword -q conversion -q visit
fi

# if necessary try to upload all other files types nos type keyword/conversion/visit
if [[ ! -s "$(cat -e $missing_files | grep -v -P "(keyword|conversion|visit)_")" ]]
then
    #Step 1: Change the data and fileType and run the command to re-load missing file.
    cd /home/xferuser/multi_client_data_feed/wfDCM
    source ../venv/bin/activate
    python anm-dcmFileProcess.py dcm_account6049 ${DATED} ALL

    #Step 2: Upload the missing file
    cd processed
    echo -e "put *" | sftp wf-prod:/'$$ id=325114'
fi
