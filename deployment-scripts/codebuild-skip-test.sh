#!/bin/bash
set -e

test_name=$1
reports_path=$2

if (( $# < 2 )); then
    echo "Missing Arguments.. Need both test_name and reports_path positional arguments to run this Script "
    exit 1
fi
upper=$(echo $test_name | tr '[:lower:]' '[:upper:]')

echo "Skipping "${upper}" Test.."
mkdir -p /tmp/reports/${reports_path}
touch /tmp/reports/${reports_path}/skipped.xml
timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
main_message="Skipped "${test_name}" as this is running in a different Environment"
echo '<?xml version="1.0" encoding="UTF-8"?><testsuite errors="0" failures="0" file="skipped" name="skipped" skipped="1" tests="1" time="0.033" timestamp="'${timestamp}'"><testcase classname="skipped" file="skipped" line="50" name="skipped" time="0.005" message="'${main_message}'" timestamp="'${timestamp}'"/></testsuite>' >> /tmp/reports/${reports_path}/skipped.xml
