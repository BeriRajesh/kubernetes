DOWNLOAD_LOCATION=${DOWNLOAD_LOCATION:-$(mktemp -d)}

files_to_download=(\
    deployment-scripts/assume-role.sh \
    deployment-scripts/codebuild-db-migrate.sh \
    deployment-scripts/codebuild-deploy.sh \
    deployment-scripts/codebuild-deployv1.sh \
    deployment-scripts/codebuild-docker-image.sh \
    deployment-scripts/codebuild-pre_build.sh \
    deployment-scripts/codebuild-run_sql_deploy_command.py \
    deployment-scripts/codebuild-run-code-minification.sh \
    deployment-scripts/codebuild-run-ecs-service-update \
    deployment-scripts/codebuild-run-lambda-update.sh \
    deployment-scripts/codebuild-run-pytest.sh \
    deployment-scripts/codebuild-run-sanity-tests.sh \
    deployment-scripts/codebuild-run-selenium-tests.sh \
    deployment-scripts/codebuild-skip-test.sh \
)

for file in ${files_to_download[@]}; do
    FNAME=$(basename ${file})
    DEST_PATH="${DOWNLOAD_LOCATION}/${FNAME}"
    echo "Downloading ${file} from repository"
    git archive --remote=git@bitbucket.org:annalect/devops.git release -- ${file} | tar -xO > ${DEST_PATH}
    chmod +x ${DEST_PATH}
done
