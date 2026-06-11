#!/bin/bash
YESTERDAY=$(date -d "1 day ago" '+%Y%m%d')
YESTERDAY_DASH=$(date -d "1 day ago" '+%Y-%m-%d')
DATED=${1:-$YESTERDAY}
DATED_DASH=${2:-$YESTERDAY_DASH}
gcp_files="/tmp/file1.txt"
sftp_files="/tmp/file2.txt"
missing_files="/tmp/file3.txt"
to_day=$(date '+%A')

echo "WellsFargo-DS3 (DoubleClickSearch)Missing Files <"$DATED">" >  $missing_files
echo "----------------------------------------------------------" >> $missing_files
echo Report_Dated: $DATED
cat /dev/null > "$gcp_files"


function validate_wf () {
for file in "${dcm_files[@]}"; do
    echo -e "$file" >> "$gcp_files"
done

echo ls -ltr | sftp wf-prod:/'$$ id=325114' | grep "$DATED". > wf-sftp-files_uploaded_today.${to_day}

if [ `echo ls | sftp wf-prod:/'$$ id=325114' | grep "$DATED". | wc -l` -ne 54 ]; then
    echo ls | sftp wf-prod:/'$$ id=325114' | grep "$DATED". > "$sftp_files"
    diff -Z "$gcp_files" "$sftp_files" |  grep "<" >> "$missing_files"

echo "" >> $missing_files
echo "" >> $missing_files
echo "TIP: You should be able to trigger a manual run remotely by running " >> $missing_files
echo "    sshg 10.5.231.240 'sudo --user xferuser -- /home/xferuser/wells_fargo/ds3/MANUAL_RUN_daemon-ds3.py -d YYYY-MM-DD -q keyword|conversion|visit [ -q keyword|conversion|visit -q ... ]''" >> $missing_files
echo "n.b. (the script activates automatically the virtualenvironment)" >> $missing_files
echo "n.b2 this script could sync ALL files executing " >> $missing_files
echo "    /home/xferuser/wells_fargo/ds3/MANUAL_RUN_daemon-ds3.py -d $DATED_DASH -q keyword -q conversion -q visit " >> $missing_files
echo "" >> $missing_files
echo "(and finally we could also change the cron to execute this monitor after 15:00 every hour)" >> $missing_files

cat $missing_files | mail -s "(MustSee)Wells Fargo :: C2T:-Missing DCM file <"$DATED">"  annalecttio@annalect.com
fi
}


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

#for file in "${dcm_files[@]}"; do
#    echo -e "$file" >> "$gcp_files"
#done
#
#if [ `echo ls | sftp wf-prod:/'$$ id=325114' | grep "$DATED". | wc -l` -ne 54 ]; then
#    echo ls | sftp wf-prod:/'$$ id=325114' | grep "$DATED". > "$sftp_files"
#    diff -Z "$gcp_files" "$sftp_files" |  grep "<" >> "$missing_files"
#
#cat $missing_files | mail -s "(MustSee)Wells Fargo :: C2T:-Missing DCM file <"$DATED">"  shashikant.kuwar@annalect.com sskuwar@gmail.com
#fi

validate_wf

#END
