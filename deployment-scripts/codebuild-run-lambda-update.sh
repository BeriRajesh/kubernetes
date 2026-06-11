#!/bin/bash
set -e

export REPOSITORY_URI="${REGISTRY_URL}"/"${IMAGE_REPO}"
export IMAGE_TAG=${IMAGE_TAG:-latest-$CODEBUILD_SOURCE_VERSION}

echo "REPOSITORY_URI is ${REPOSITORY_URI}"
echo IMAGE_TAG is $IMAGE_TAG

function update_lambda () {
	LAMBDA_FUNCTION_NAME="${APP_NAME}-${BUILD_ENV}"

	CURRENT_VERSION=$(aws --output json lambda get-function --function-name ${LAMBDA_FUNCTION_NAME} --qualifier release  --query Configuration.Version | bc)

	# aws lambda update-function-code \
	# 	--function-name ${LAMBDA_FUNCTION_NAME} \
	# 	--image-uri "${REPOSITORY_URI}:${IMAGE_TAG}" \
	# 	--publish > OUTPUT

	# updating code n times
	set +e
	n=2

	echo "Executing update-function-code '$n' times"
	while [ $n -gt 0 ]; do
		aws lambda update-function-code \
				--function-name ${LAMBDA_FUNCTION_NAME} \
				--image-uri "${REPOSITORY_URI}:${IMAGE_TAG}" \
				--publish > OUTPUT

		exit_code=$?
		echo "exit code was: $exit_code"
		echo "output was:"
		cat OUTPUT
		if [ "$exit_code" -eq 0 ]; then
			n=$(($n-1))
			echo "Executing $n more times"
		fi
		sleep 5
	done
	set -e


	NEW_VERSION=$(cat OUTPUT | jq .Version | bc)

	# if [ $NEW_VERSION == $CURRENT_VERSION ]; then
	# 	NEW_VERSION=$(echo $NEW_VERSION + 1 | bc)
	# fi
	echo "upgrading from '${CURRENT_VERSION}' to '${NEW_VERSION}'..."

	until aws lambda update-alias --function-name ${LAMBDA_FUNCTION_NAME} --name release --function-version ${NEW_VERSION}; do
		echo "waiting to update the function"
		sleep 5;
	done;
}

# Excute called function
$1