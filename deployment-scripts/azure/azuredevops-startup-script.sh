#!/bin/bash
mkdir -p ~/.ssh

# Bitbucket ReadOnly Permission
echo "$(id-rsa)" > ~/.ssh/id_rsa && chmod 600 ~/.ssh/id_rsa
ssh-keyscan bitbucket.org >>~/.ssh/known_hosts

# Download Secret Entrypoint from a central location
git archive --remote=git@bitbucket.org:annalect/devops.git release -- deployment-scripts/azure/secrets-entrypoint.sh | tar -xO > secrets-entrypoint.sh

#Permissions for Secret Entrypoint file
chmod u+x secrets-entrypoint.sh

#Updating the Dockerfile
sed -i '/CMD/d' Dockerfile
echo 'RUN chmod +x secrets-entrypoint.sh' >> Dockerfile
echo 'ENTRYPOINT ["sh", "secrets-entrypoint.sh"]' >> Dockerfile