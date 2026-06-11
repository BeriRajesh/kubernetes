#!/bin/bash

#set -x

#curl -H 'Authorization: Bearer JWT' -H 'Content-Type: application/json' 'https://devinvestment-planner.api.annalect.com/plans/client/59b64e84-15b3-11e9-8be3-124543dc7c0c/'

clear

# INVESTMENT PLANNER
    # # DEV
    # NAME="INVESTMENT PLANNER DEV"
    # CF_URL="https://devinvestment-planner.api.annalect.com"
    # APIGW_URL="https://ytsmr3s317.execute-api.us-east-1.amazonaws.com"
    # CLIENT="plans/client/59b64e84-15b3-11e9-8be3-124543dc7c0c/"
    # GENERATE_TOKEN_URL="https://framework-template-api.accuenplatform.com/token/59b64e84-15b3-11e9-8be3-124543dc7c0c/"

    # # PROD
    # NAME="INVESTMENT PLANNER PROD"
    # CF_URL=https://investment-planner.api.annalect.com
    # APIGW_URL=https://pv1wtsmxt7.execute-api.us-east-1.amazonaws.com
    # CLIENT=plans/client/59b64e84-15b3-11e9-8be3-124543dc7c0c/
    # GENERATE_TOKEN_URL="https://framework-template-api.accuenplatform.com/token/59b64e84-15b3-11e9-8be3-124543dc7c0c/"

# CHANNEL PLANNER
    # # PROD
    # NAME="CHANNEL PLANNER PROD"
    # CF_URL="https://channel-planner.api.annalect.com"
    # APIGW_URL="https://d3tq7vigjb.execute-api.us-east-1.amazonaws.com"
    # CLIENT="plans/client/59b64e84-15b3-11e9-8be3-124543dc7c0c/"
    # GENERATE_TOKEN_URL="https://framework-template-api.accuenplatform.com/token/59b64e84-15b3-11e9-8be3-124543dc7c0c/"

    # DEV
    # NAME="CHANNEL PLANNER DEV"
    # CF_URL="https://devchannel-planner.api.annalect.com"
    # APIGW_URL="https://03asgyqph0.execute-api.us-east-1.amazonaws.com"
    # CLIENT="plans/client/4359f5cc-6569-11e9-bc97-12cc0f0e8006/"
    # GENERATE_TOKEN_URL="https://framework-template-api.accuenplatform.com/token/4359f5cc-6569-11e9-bc97-12cc0f0e8006/"

# SHARED OBJECTS API
    # # DEV
    # NAME="SHARED OBJECTS API DEV1"
    # CF_URL="https://devshared-objects.api.annalect.com"
    # APIGW_URL="https://63ohyhjxjh.execute-api.us-east-1.amazonaws.com"
    # CLIENT="/headers"
    # GENERATE_TOKEN_URL="https://framework-template-api.accuenplatform.com/token/59b64e84-15b3-11e9-8be3-124543dc7c0c/"
    # METHOD="PUT"
    # TEST_MSSQL=false

    # # DEV2
    # NAME="SHARED OBJECTS API DEV2"
    # CF_URL="https://devshared-objects.api.annalect.com"
    # APIGW_URL="https://63ohyhjxjh.execute-api.us-east-1.amazonaws.com"
    # CLIENT="headers"
    # GENERATE_TOKEN_URL="https://framework-template-api.accuenplatform.com/token/59b64e84-15b3-11e9-8be3-124543dc7c0c/"
    # METHOD="PUT"
    # TEST_MSSQL=false

    # # DEV3
    # NAME="SHARED OBJECTS API DEV3"
    # CF_URL="https://devshared-objects.api.annalect.com"
    # APIGW_URL="https://63ohyhjxjh.execute-api.us-east-1.amazonaws.com"
    # CLIENT="omni_object/2855712e-65e3-47db-a333-666e6bd3a95c/bulk/?data_fields=name,status,updated_at,smp_group,avg_clearing_price,thirty_day_avails,thirty_day_uniques&smp_group=109&length=all"
    # GENERATE_TOKEN_URL="https://framework-template-api.accuenplatform.com/token/59b64e84-15b3-11e9-8be3-124543dc7c0c/"
    # METHOD="POST"
    # TEST_MSSQL=false
    # DATA='{"name":"name", "id":"external_id", "status.omg_channel_status_label":"status", "updated_at":"update_date", "smp_group_id":"permissions", "data_points":["avg_clearing_price","thirty_day_avails","thirty_day_uniques"]}'

    # # QA
    # NAME="SHARED OBJECTS API QA"
    # CF_URL="https://qashared-objects.api.annalect.com"
    # APIGW_URL="https://c6pc7blnoe.execute-api.us-east-1.amazonaws.com"
    # CLIENT="omni_object/2855712e-65e3-47db-a333-666e6bd3a95c/bulk/?data_fields=name,status,updated_at,smp_group,avg_clearing_price,thirty_day_avails,thirty_day_uniques&smp_group=109&length=all"
    # GENERATE_TOKEN_URL="https://framework-template-api.accuenplatform.com/token/59b64e84-15b3-11e9-8be3-124543dc7c0c/"
    # METHOD="POST"
    # TEST_MSSQL=false
    # DATA='{"name":"name", "id":"external_id", "status.omg_channel_status_label":"status", "updated_at":"update_date", "smp_group_id":"permissions", "data_points":["avg_clearing_price","thirty_day_avails","thirty_day_uniques"]}'

    # STG
    NAME="SHARED OBJECTS API STG"
    CF_URL="https://stgshared-objects.api.annalect.com"
    APIGW_URL="https://nwa55t5woe.execute-api.us-east-1.amazonaws.com"
    CLIENT="token/5a0e1d3f-29fa-4e89-b1ea-c7626fde71e5/"
    GENERATE_TOKEN_URL="https://framework-template-api.accuenplatform.com/token/59b64e84-15b3-11e9-8be3-124543dc7c0c/"
    METHOD="POST"
    TEST_MSSQL=false
    DATA="{\"username\":\"$SSO_USERNAME\",\"password\":\"$SSO_PASSWORD\",\"expires_in\":1440,\"env\":\"\"}"


METHOD=${METHOD:-"GET"}
TEST_MSSQL=${TEST_MSSQL:-"true"}
DATA=${DATA:-}

echo "Testing $NAME"

echo "generating token with: curl -H 'Content-Type: application/json' '$GENERATE_TOKEN_URL'"
echo
TOKEN=$(curl -H 'Content-Type: application/json' "$GENERATE_TOKEN_URL")

echo
echo "-------------------------------------------------------------------"

echo "Checking cloudfront: $CF_URL"
curl "$CF_URL"
echo
echo "-------------------------------------------------------------------"

if [ $TEST_MSSQL = true ]; then
    echo "Checking MSSQL With cloudfront URL: $CF_URL/mssql"
    curl "$CF_URL/mssql"
    echo
    echo "-------------------------------------------------------------------"
fi

if [ -z "${DATA}" ]; then
    echo HERE
    echo "testing token cf at $CF_URL/$CLIENT with curl w/o DATA"
    echo
    curl -X$METHOD -H "Authorization: Bearer $TOKEN" "$CF_URL/$CLIENT"
    echo
    echo "-------------------------------------------------------------------"
else
    echo THERE
    echo "testing token cf at $CF_URL/$CLIENT with curl WITH DATA"
    echo
    curl -X$METHOD -d "$DATA" -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" "$CF_URL/$CLIENT"
    echo
    echo "-------------------------------------------------------------------"
fi


echo "Checking apigw: $APIGW_URL"
curl "$APIGW_URL"
echo
echo "-------------------------------------------------------------------"

if [ $TEST_MSSQL = true ]; then
    echo "Checking MSSQL with apigw: $APIGW_URL/mssql"
    curl "$APIGW_URL/mssql"
    echo
    echo "-------------------------------------------------------------------"
fi

if [ -z "${DATA}" ]; then
    echo HERE
    echo "testing token apigw: $APIGW_URL/$CLIENT with curl w/o DATA"
    echo
    curl -X$METHOD -H "Authorization: Bearer $TOKEN" "$APIGW_URL/$CLIENT"
    echo
    echo "-------------------------------------------------------------------"
else
    echo THERE
    echo "testing token apigw: $APIGW_URL/$CLIENT WITH DATA"
    echo
    curl -X$METHOD -d "$DATA" -H 'Content-Type: application/json' -H "Authorization: Bearer $TOKEN" "$APIGW_URL/$CLIENT"
    echo
    echo "-------------------------------------------------------------------"
fi

