#!/bin/bash
set -e

# bugfix
PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:$PATH"

# write stdout and stderr to syslog, using logger.
# taken from: http://urbanautomaton.com/blog/2014/09/09/redirecting-bash-script-output-to-syslog/
exec 1> >(logger -s -t $(basename $0)) 2>&1

### Takes backup of wordpress site folder with a database dump inside
### Requirements:
###     * WP-CLI (it gets installed if not present)
###
### Usage:
### $ ./backup_site.sh </path/to/site> <prefix after "annalect-backups/wordpress/" in s3>

function install_wpcli() {
    pushd /opt
    curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
    mv wp-cli.phar wp-cli
    chmod +x wp-cli
    popd
}

# defining full path of needed binaries
AWS=$(which aws)
GZIP=$(which gzip)
TAR=$(which tar)
RM=$(which rm)


# defining variables
aws_region="us-east-1"
sitename="$1"
# stripping starting and ending slashes and spaces
s3_prefix=$(echo $2 | perl -pe 's/\/?\s*$//g and s/^\s*?\/?//g')
timestamp=$(date +%Y%m%d-%H%M)
wordpress_basename=$(basename $sitename)
wordpress_backup_basename_db="${wordpress_basename}-backup-db"
wordpress_backup_basename_site="${wordpress_basename}-backup-site"

wordpress_backup_name_db="${wordpress_backup_basename_db}-${timestamp}.sql"

wordpress_backup_name_db_compressed="${wordpress_backup_name_db}.gz"
wordpress_backup_name_site_compressed="${wordpress_backup_basename_site}-${timestamp}.tar.gz"


# some validations
if [ -z "$sitename" ] || [ -z "$s3_prefix" ]; then
    echo -e "\nERROR: Site to backup must be specified as a first parameter, and s3 prefix as second parameter."
    echo -e "Usage:"
    echo -e "\t$ ./backup_site.sh </path/to/site> <prefix after 'annalect-backups/wordpress/' in s3>"
    echo -e "Example:"
    echo -e "\t$ ./backup_site.sh /var/www/annalectde dev.annalect.de"
    exit 1
fi;

if [ ! -d "$sitename" ]; then
    echo "\$sitename='$sitename' is not a valid path."
    exit 1
fi;


# verify if WP-CLI is installed for user
WPCLI='/opt/wp-cli'

if [ ! -f "$WPCLI" ]; then
    install_wpcli
else
    echo "WP-CLI found in $WPCLI!"
fi

# update WP-CLI
$WPCLI cli update || true

pushd $sitename

echo "Removing old database backups"
$RM -f ${wordpress_backup_basename_db}* || true

echo "Taking dump of ${wordpress_basename}'s DB and compressing"
$WPCLI --allow-root db export --quiet ${wordpress_backup_name_db}
$GZIP ${wordpress_backup_name_db}

pushd ..

echo "Making backup of ${sitename} (with DB dump inside)"
$TAR czf ${wordpress_backup_name_site_compressed} ${wordpress_basename}

echo "Uploading site's backup to AWS"
$AWS --region ${aws_region} s3 cp ${wordpress_backup_name_site_compressed} s3://annalect-backups/wordpress/${s3_prefix}/ --sse > /dev/null

echo "Deleting local copy of site's backup"
$RM -f ${wordpress_backup_name_site_compressed}

popd
echo "Done! Have a good day, sir!"
