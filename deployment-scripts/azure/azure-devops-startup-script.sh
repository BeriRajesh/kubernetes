#!/bin/bash
mkdir -p ~/.ssh

# Bitbucket ReadOnly Permission
echo "$(id-rsa)" > ~/.ssh/id_rsa && chmod 600 ~/.ssh/id_rsa
ssh-keyscan bitbucket.org >>~/.ssh/known_hosts

# Download Secret Entrypoint from a central location
git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/azure/secrets-entrypoint-mcs.sh | tar -xO > secrets-entrypoint-mcs.sh

#Permissions for Secret Entrypoint file
chmod u+x secrets-entrypoint.sh

#Updating the Dockerfile
sed -i '/CMD/d' Dockerfile
sed -i '/ENTRYPOINT/d' Dockerfile
echo 'RUN chmod +x secrets-entrypoint-mcs.sh' >> Dockerfile
echo 'ENTRYPOINT ["sh", "secrets-entrypoint-mcs.sh"]' >> Dockerfile