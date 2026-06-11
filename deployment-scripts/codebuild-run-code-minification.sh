#!/bin/bash
set -e

#### Some possible environment variables:
## All variables are optional
# getCodeVersion=true|false: to generate a __version file. default to false.
# MINIFY_CODE=true|false: to run `npm ci`. Default 'false'.
# GRUNT_MINIFY_CODE=true|false: if to run `grun build`. Default false.
# GRUNTFILE: specify a gruntfile. Default `gruntfile.js`
####

# REMEMBER TO:
# 1. keep space between variables
# 2. Change approproate branch name
###

#### no need to modify below this comment ####
#######################################################################


# #### no need to modify below this comment ####

# # dowload script
# SCRIPT_PATH=deployment-scripts
# SCRIPT_NAME=codebuild-pre_build.sh
# git archive --remote=git@bitbucket.org:annalect/devops.git release -- ${SCRIPT_PATH}/${SCRIPT_NAME} | tar -xO > ${SCRIPT_NAME}
# chmod +x ${SCRIPT_NAME}

# cat ${SCRIPT_NAME}

# # execute script
# # ./${SCRIPT_NAME}

# SCRIPT_PATH=deployment-scripts
# SCRIPT_NAME=codebuild-pre_build.sh
# git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/codebuild-pre_build.sh | tar -xO > codebuild-pre_build.sh
# chmod +x codebuild-pre_build.sh && ./codebuild-pre_build.sh

echo "Running as: '$(whoami)'"


#Get Latest Code Version and insert into Docker Build
if [ "${getCodeVersion}" = "true" ]; then
	version=$(git log | head -n1 || true)
	date=$(date --iso-8601=seconds || true)
    md5sum=$(md5sum serverbase.cfg || true)
    remote=$(git remote -v | head -n1 | cut -f2 | awk '{print $1}')
    json="{\"version\": \"${version:-}\", \"date\": \"${date:-}\", \"remote\":\"${remote:-}\", \"md5sum-serverbase\":\"${md5sum:-}\"}"

	if [ -d "src/static" ]; then
		echo $json > src/static/__version.json || true
	else
		echo $json > __version.json || true
	fi
fi

# grunt minification
if [ "${GRUNT_MINIFY_CODE}" = "true" ]; then
	echo "Starting grunt minification..."
	GRUNTFILE=${GRUNTFILE:-gruntfile.js}
	if [ ! -z ${GRUNTFILE} ]; then GRUNTFILE="--gruntfile ${GRUNTFILE}"; fi
	npm install
	grunt ${GRUNTFILE} build
	echo "Grunt minification completed..."
else
	echo "Grunt minification is disabled"
fi

#minify code on npm run build
if [ "${MINIFY_CODE}" = "true" ]; then
	echo "Starting minification..."
	npm ci && npm run build:ci || npm run build
	echo "Minification completed..."
else
	echo "Minification is disabled"
fi
