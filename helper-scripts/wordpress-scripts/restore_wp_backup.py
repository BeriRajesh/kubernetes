#!/usr/bin/env python3

"""
Script to restore Wordpress Backups taken with `ansible_update.yml` playbook

The format of these backups are:
    - A compressed .tar.gz file of the whole wordpress folder
    - Inside the folder there is the corresponding DB dump
    - The name of the backup
"""
import datetime
import glob
import os
import readline
import subprocess
import sys


try:
    from halo import Halo
except ImportError as e:
    print("Python's module Halo not found. Include it for better a experience.")
    class spinner:
        def start(self, str):
            print(str)
        def succeed(self):
            pass
    spinner = spinner()

#try:
    # from botocore.exceptions import ClientError

import argparse
import boto3
import sh
#except ImportError as e:
    #print('Please install all the dependencies: pip3 install argparse boto3 halo readline sh ')
    #sys.exit(e)

parser = argparse.ArgumentParser(
    description='Restores wordpress backups (made with the ansible_update.yml` playbook. Depends on WP-CLI command.')
# parser.add_argument("action", choices=['sync', 'check'], nargs='?', default='sync',
#                     help="action to perform (default sync)")
# parser.add_argument("-v", "--verbose", default=0,
#                     help="increase output verbosity", action='count')
parser.add_argument("-w", "--wpcli-full-filename", default='',
                    help="Full /path/to/filename to the WP-CLI binary to use")

parser.add_argument("-s", "--source", default='',
                    help="Path in S3 to backup, after annalect-backups:wordpress/")

parser.add_argument("-f", "--file", default='',
                    help="Use this path/to/file.tar.gz file instead of downloading from AWS S3")

parser.add_argument("-d", "--dir", default='',
                    help="Use this path/to/directory instead of downloading from AWS S3")
# parser.add_argument("-c", "--config", default='',
#                     help="config file to use with 'rclone' tool (rclone --help for more info)]")
# parser.add_argument("-i", "--interactive", default='',
#                     help="presents a prompt before executing copying commands to source files", action='store_true')
#
args = parser.parse_args()


def s3_get_file(bucket, path, destination, callback=None, **kwargs):
    boto3_session = boto3.session.Session(**kwargs)
    s3 = boto3_session.client('s3')
    with open(destination, 'wb') as fh:
        s3.download_fileobj(bucket, path, fh, Callback=callback)


def get_wpcli_path():
    wp_cli = args.wpcli_full_filename
    if not wp_cli or not os.path.exists(wp_cli):
        wpcli_names = ['wp', 'wp-cli']
        for possible_bin in wpcli_names:
            try:
                wp_cli = subprocess.check_output('which {}'.format(possible_bin), shell=True,
                                                 stderr=subprocess.STDOUT) \
                    .decode('utf-8').strip('\n')
            except subprocess.CalledProcessError:
                continue
            if wp_cli != "":
                break
        else:
            for possible_bin in wpcli_names:
                if os.path.isfile(possible_bin):
                    wp_cli = os.getcwd() + '/' + possible_bin
                    break
            else:
                sys.exit("""
                No WP-CLI binary could be found installed on the server (using `which`) or in the current path.

                Please install with

                    $ curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar
                    $ mv wp-cli.phar wp && chmod +x wp

                and then re-run this script.
                """)

    return {"wpcli": wp_cli}


def callb(s):
    print('.', end="", flush=True)


def print_wp_credentials(destination_path):
    old_path = os.getcwd()
    os.chdir(destination_path)
    try:
        # print(wpcli('config', 'list'))
        # db_user = wpcli('config', 'get', 'DB_USER')
        db_name = wpcli('config', 'get', 'DB_NAME').strip()
        # db_password = wpcli('config', 'get', 'DB_PASSWORD')
        db_host = wpcli('config', 'get', 'DB_HOST').strip()
        print("This is the DB info of wordpress in '{}':".format(destination_path))
        print("    DB_NAME: {}\n    DB_HOST: {}\n".format(db_name, db_host))
    except sh.ErrorReturnCode_1 as e:
        print('WP-CLI gave an error {}'.format(e))
        return False, None, None, None, None
    finally:
        os.chdir(old_path)


def verify_wp(destination_path, **kwargs):
    # print('Verifying wordpress installation at {}'.format(destination_path))
    old_path = os.getcwd()
    os.chdir(destination_path)
    try:
        if "print" in kwargs and kwargs["print"]:
            print(wpcli('config', 'list'))
        db_user = wpcli('config', 'get', 'DB_USER').strip()
        db_name = wpcli('config', 'get', 'DB_NAME').strip()
        db_password = wpcli('config', 'get', 'DB_PASSWORD').strip()
        db_host = wpcli('config', 'get', 'DB_HOST').strip()
    except sh.ErrorReturnCode_1 as e:
        print('WP-CLI gave an error {}'.format(e))
        input('Verify the information. Press enter if you wish to continue.')
        return False, None, None, None, None
    finally:
        os.chdir(old_path)

    return True, db_user, db_name, db_password, db_host


def get_source():
    if not args.source and not args.file and not args.dir:
        source = input('Input full path/to/backup/filename.tar.gz or folder name of the backup located in '
                       's3://annalect-backups/wordpress/ : ')
    else:
        source = args.source

    return source


def get_backup_files(source_name):
    backup_destination_dir = 'backup-restore-{}/'.format(backup_timestamp)
    backup_filename = 'backup-to-restore.tar.gz'
    backup_destination_filename = backup_destination_dir + backup_filename

    if not args.dir and not os.path.exists(backup_destination_dir):
        print('Creating temporary path to download backup: {}'.format(backup_destination_dir))
        os.mkdir(backup_destination_dir)
        backup_destination_dir = os.path.abspath(backup_destination_dir)

    uncompress_file = None
    if source_name:
        download_path = "wordpress/" + source_name
        if download_path[-7:] == '.tar.gz':
            try:
                spinner.start("Fetching from AWS `{}` ... ".format(download_path))
                s3_get_file('annalect-backups', download_path, backup_destination_filename)
            except ClientError:
                sys.exit('Error: Backup was not found in S3')
            finally:
                spinner.succeed()

            # os.chdir(backup_destination_dir)
            uncompress_file = backup_destination_filename
        else:
            sh.aws('s3', 'sync', 's3://annalect-backups/{}'.format(download_path), backup_destination_dir)
    elif args.file:
        if not os.path.isfile(args.file):
            sys.exit('Error: file {} is not valid.'.format(args.file))

        spinner.start("Copying file `{}` to `{}` ... ".format(args.file, backup_destination_dir))
        sh.cp(args.file, backup_destination_filename)
        spinner.succeed()
        uncompress_file = backup_destination_filename
    elif args.dir:

        if not os.path.isdir(args.dir):
            sys.exit('Error: path {} is not valid.'.format(args.dir))
        backup_destination_dir = args.dir

        # if args.dir[-1] != '/':
        # args.dir += '/'

        # # database_backups = glob.glob(args.dir + '*.sql.gz')
        # # if len(database_backups) != 1:
        # # sys.exit('Error: no .sql.gz db dumps found found ending in `{}`, or more than 1 found. Refusing to '
        # # 'use this folder'.format(args.dir))

        # spinner.start("Rsyncing files from path `{}` to `{}` ... ".format(args.dir, backup_destination_dir))
        # sh.rsync('-iva', args.dir, backup_destination_dir)
        # spinner.succeed()

    if uncompress_file and os.path.isfile(uncompress_file):
        spinner.start("Uncompressing file `{}` ... ".format(uncompress_file))
        sh.tar('xzf', uncompress_file, '-C', backup_destination_dir, '--strip-components', '1')
        spinner.succeed()

    return os.path.abspath(backup_destination_dir)


def backup_db(destination_path):
    old_path = os.getcwd()
    try:
        os.chdir(destination_path)

        db_name = wpcli('config', 'get', 'DB_NAME').strip()
        db_backup_name = 'db-backup-{}-{}.sql'.format(db_name, backup_timestamp)

        msg = 'Creating backup of current database in {} ("{}") as "{}"'.format(destination_path, db_name,
                                                                                db_backup_name)
        spinner.start(msg)
        wpcli.db('export', db_backup_name)
        spinner.succeed()

        print('Check database backup size. Press enter if you wish to continue:')
        print(sh.ls('-lhrt', db_backup_name))
    except:
        print('error, --- no files ---')
        if input('continue (y/N)?') != 'y':
            sys.exit()
    finally:
        os.chdir(old_path)


def restore_backup(**kwargs):
    # backup old folder to be replaced
    # get backup to be restored from s3
    # uncompress backup to temp folder like temp/<uncompressed wordpress foldername>/<files....>
    # uncompress <db dump>
    # get <current db name> from wp config
    # export <current db> to file (as a backup)
    # drop <current db>
    # restore <db dump> to <current db name>
    # replace old site with backup

    # restore_over_valid_wordpress = kwargs['restore_over_valid_wordpress']
    source_name = kwargs['source_name']
    destination_path = kwargs['destination_path']
    # backup_destination_dir = kwargs['backup_destination_dir']
    # backup_destination_filename = kwargs['backup_destination_filename']

    # db_replace_old = kwargs['db_replace_old']
    # new_db_name = kwargs['new_db_name']
    # new_db_username = kwargs['new_db_username']
    # new_db_password = kwargs['new_db_password']

    # if not os.path.exists(destination_path):
    # sys.exit('Destination path `{}` does not exist on this server'.format(destination_path))

    # download/uncompress/fetch backup files from source_name
    backup_destination_dir = get_backup_files(source_name)

    # verify presence of backup db
    database_backups = glob.glob(backup_destination_dir + '/*.sql.gz')
    if len(database_backups) == 0:
        sys.exit('Error: No .sql.gz database dumps found `{}`'.format(backup_destination_dir))
    elif len(database_backups) > 1:
        sys.exit(
            "The path '{}' has more than one db dumps with extension .sql.gz. Please leave only one and restart the "
            "restore script with option '-d {}' to use this folder".format(
                backup_destination_dir, backup_destination_dir))

    database_backup = database_backups[0]

    print("Found `{}`, assuming this file as the database dump of the backup".format(database_backup))

    print_wp_credentials(backup_destination_dir)

    # if destination_path exists, we create backups
    old_valid_wp = False
    old_db_name = None
    old_db_user = None
    old_db_password = None
    if os.path.exists(destination_path):
        destination_path = os.path.abspath(destination_path)
        # print("Path '{}' exists. Making backup...".format(destination_path))

        old_valid_wp, old_db_user, old_db_name, old_db_password, old_db_host = verify_wp(destination_path)
        if old_valid_wp:
            # print_wp_credentials(destination_path)
            if input("Backup database of wordpress in '{}'? (Y/n): ".format(destination_path, old_db_name)) == 'n':
                print('Backup of current db will not be created!')
            else:
                backup_db(destination_path)

        # backing up destination_path folder
        backup_folder = '{}-{}'.format(destination_path, backup_timestamp)
        ## renaming original folder to timestamped name
        spinner.start('Renaming folder {} to {}'.format(destination_path, backup_folder))
        sh.mv(destination_path, backup_folder)
        spinner.succeed()

    ## renaming backup to original folder name
    spinner.start('Renaming folder {} to {}'.format(backup_destination_dir, destination_path))
    sh.mv(backup_destination_dir, destination_path)
    spinner.succeed()

    destination_path = os.path.abspath(destination_path)
    os.chdir(destination_path)

    print("Resetting backup's DB information to old wordpress installation")
    wpcli('config', 'set', 'DB_NAME', old_db_name)
    wpcli('config', 'set', 'DB_USER', old_db_user)
    wpcli('config', 'set', 'DB_PASSWORD', old_db_password)
    wpcli('config', 'set', 'DB_HOST', old_db_host)

    # if old_valid_wp and input("Use old db credentials? (Y/n) \nDB_NAME: {}\nDB_USER: {}\nDB_PASSWORD: {}\nDB_HOST:
    # {}\n? ".format(old_db_name,old_db_user,old_db_password,old_db_host)) != 'n':
    # wpcli('config','set','DB_NAME', old_db_name)
    # wpcli('config','set','DB_USER', old_db_user)
    # wpcli('config','set','DB_PASSWORD', old_db_password)
    # wpcli('config','set','DB_HOST', old_db_host)
    # else:
    # sys.exit("Specifying new credentials is not yet supported")

    print_wp_credentials(destination_path)
    input("continue?")

    db_backup_basename = os.path.basename(database_backup)
    spinner.start('Un-compressing db backup `{}` ...'.format(db_backup_basename))
    sh.gzip('-d', db_backup_basename)
    spinner.succeed()

    spinner.start('Resetting DB {}'.format(old_db_name))
    wpcli('db', 'reset', '--yes')
    spinner.succeed()

    # input('Import backup? (enter to continue)')
    spinner.start('Importing db from backup ...')
    wpcli('db', 'import', db_backup_basename[:-3])
    spinner.succeed()

    print("Removing files {} and {}".format(db_backup_basename, backup_filename))
    os.remove(db_backup_basename)
    os.remove(backup_filename)

    print('END!')


if __name__ == "__main__":
    # instantiating objects
    spinner = Halo()

    # defining some variables
    backup_timestamp = '{0:%Y%m%d__%H%M%S}'.format(datetime.datetime.now())

    # get the source backup either from options -s, -f or -d or through input()
    source_name = get_source()

    # this is where files are going to be restored
    destination_path = input('Input the path where the backup is to be restored (wordpress installation to substitute '
                             'with backup): ')

    destination_path = os.path.abspath(destination_path)

    # if destination_path[-1] != '/':
    # destination_path += '/'

    # setting up WP-CLI command
    wp_cli_path = get_wpcli_path()
    wpcli = sh.php.bake(wp_cli_path['wpcli'], '--allow-root')

    # # check if we are substituting a current wordpress installation
    # db_replace_old = True
    # valid_wp, db_user, db_name, db_password, db_host = verify_wp(destination_path)
    # if valid_wp and input("There is an existing wordpress installation in the restoration path. Overwrite existing
    # database with backup's contents (Y/n)?") == 'n':
    # db_replace_old = False

    # new_db_name = None
    # new_db_username = None
    # new_db_password = None
    # if not db_replace_old or not valid_wp:
    # new_db_name = input('Please specify a database name (has to exist) to restore data from the backup ({}):
    # '.format(db_name)) or db_name
    # # if not new_db_name:
    # # sys.exit('Error: new db name must be specified')

    # new_db_username = input('Please specify a username database name (has to exist) to restore database from '
    # 'backup. This database must allow current WPUSER to create tables ({}): '
    # .format(db_user)) or db_user
    # new_db_password = input('Please specify the password for the user ({}): '.format(db_password)) or db_password

    restore_backup(
        # restore_over_valid_wordpress=valid_wp,
        source_name=source_name,
        destination_path=destination_path,
        # backup_destination_dir=backup_destination_dir,
        # backup_destination_filename=backup_destination_filename,
        # db_replace_old=db_replace_old,
        # new_db_name=new_db_name,
        # new_db_username=new_db_username,
        # new_db_password=new_db_password,
    )

