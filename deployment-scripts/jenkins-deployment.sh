#!/bin/bash
set -e
### Versions
# 2022-09-19 - replacing 'branch_to_replace' with 'branch_to_replace_with', but with the current checked out branch being 'branch_to_replace'
###

#### Some possible environment variables:
## All variables are optional
# branch_to_replace_with=empty|<branch_name>: target branch. Default 'empty'.
# branch_to_replace=empty|<branch_name>: source branch.  Default 'empty'
# getCodeVersion=true|false: to generate a __version file. default to false.
# MINIFY_CODE=true|false: to run `npm ci`. Default 'false'.
# GRUNT_MINIFY_CODE=true|false: if to run `grun build`. Default false.
# GRUNTFILE: specify a gruntfile. Default `gruntfile.js`
####

# REMEMBER TO:
# 1. keep space between variables
# 2. Change appropriate branch name
###

#### no need to modify below this comment ####
#######################################################################


# #### no need to modify below this comment ####

# # dowload script
# SCRIPT_NAME=bamboo-deploy.sh
# git archive --remote=git@bitbucket.org:annalect/devops.git release -- ${SCRIPT_NAME} | tar -xO > ${SCRIPT_NAME}
# chmod +x ${SCRIPT_NAME}

# cat ${SCRIPT_NAME}

# # execute script
# # ./${SCRIPT_NAME}

echo "Running as: '$(whoami)'"

# copying private key for pylect-infra
#echo "Copying deployment key"
#cp /root/docker-deployments.key . || true
#if [ -f "docker-deployments.key" ]; then
#	echo "Deployment key in place."
#else
#	echo "Deployment key not found."
#fi

# Get the currently logged-in username
current_user=$(whoami)



#repo=$(echo $bamboo_planRepository_repositoryUrl | awk -F 'org/' '{print $2}')
repo=${repo:-}
repo_url=git@bitbucket.org:"${repo}"
echo "Working with repo_url: ${repo_url}"

#######
# no need to modify below this line

# initializing default value for variables
remote=central
branch_to_replace=${branch_to_replace:-}
branch_to_replace_with=${branch_to_replace_with:-}
getCodeVersion=${getCodeVersion:-"true"}
MINIFY_CODE=${MINIFY_CODE:-"false"}
MAKE_BACKUP=${MAKE_BACKUP:-"true"}
replace_branch=${replace_branch:-"yes"}

echo "remote=$remote"
echo "branch_to_replace=$branch_to_replace"
echo "branch_to_replace_with=$branch_to_replace_with"
echo "getCodeVersion=$getCodeVersion"
echo "MINIFY_CODE=$MINIFY_CODE"
echo "MAKE_BACKUP=$MAKE_BACKUP"
echo "replace_branch=$replace_branch"

# removing/adding remote
echo "Fetching remote '${remote}'"
git remote rm ${remote} || true
git remote add ${remote} ${repo_url}

if [ -z "${branch_to_replace}" ]; then
    echo "Environment variable 'branch_to_replace' was not specified. Not taking backup of branch, nor replacing branch."
else
	# backup branch
	git fetch ${remote} ${branch_to_replace}
	backup_branch_name="bamboo-backup-${branch_to_replace}"
	if [ "${MAKE_BACKUP}" = "true" ]; then
		echo "Backup branch ${remote}/${branch_to_replace} to refs/heads/${backup_branch_name}"
		git push -f ${remote} ${remote}/${branch_to_replace}:refs/heads/${backup_branch_name}
	else
		echo "Variable MAKE_BACKUP != true. Not making backup."
	fi
	if [ -z "${branch_to_replace_with:-}" ] || [ ! ${replace_branch} == "yes" ]; then
		echo "replace_branch=${replace_branch}"
		echo "branch_to_replace_with=${branch_to_replace_with}"
		echo "Environment variable 'branch_to_replace_with' was not specified or customization variable replace_branch is different from 'yes'."
	else
		echo "Fetching from ${remote} branch ${branch_to_replace_with}"
		git fetch -f ${remote} ${branch_to_replace_with}

		# replace branch
		echo "Replacing branch ${branch_to_replace} with ${remote}/${branch_to_replace_with}"
		git push -f ${remote} ${remote}/${branch_to_replace_with}:${branch_to_replace}

        # update local files
		echo "Updating local files"
        git pull -f ${remote} ${branch_to_replace}

        # remove extraneous files
		echo "Removing extraneous files"
        git clean -fd
	fi
fi

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
GRUNTFILE=${GRUNTFILE:-gruntfile.js}
if [ ! -z ${GRUNTFILE} ]; then
	GRUNTFILE="--gruntfile ${GRUNTFILE}"
fi
if [ "${GRUNT_MINIFY_CODE}" = "true" ]; then
	echo "Starting grunt minification..."
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