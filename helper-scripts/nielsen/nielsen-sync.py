#!/usr/bin/env python3.4

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys

os.chdir(os.path.realpath(os.path.dirname(__file__)))
sys.path.append('../')
import lib.helper_functions as hf

parser = argparse.ArgumentParser(
    description='Synchronizes file using `rclone`, `aws` and `unzip` tools between an FTP configured already in rclone '
                'and AWS s3')
parser.add_argument("action", choices=['sync', 'check'], nargs='?', default='sync',
                    help="action to perform (default sync)")
parser.add_argument("-v", "--verbose", default=0,
                    help="increase output verbosity", action='count')
parser.add_argument("-p", "--profile", default='',
                    help="aws profile to use")
parser.add_argument("-c", "--config", default='',
                    help="config file to use with 'rclone' tool (rclone --help for more info)]")
parser.add_argument("-i", "--interactive", default='',
                    help="presents a prompt before executing copying commands to source files", action='store_true')

args = parser.parse_args()


def binaries_info():
    return 'Using binaries: \n\taws:`{}` \n\trclone:`{}` \n\tunzip:`{}`'.format(
        aws_binary_path,
        rclone_binary_path,
        unzip_binary_path
    )


def get_file_list():
    """Get a list of zip files from the namft.nielsen.com FTP """
    output = subprocess.check_output(rclone_binary_path + ' ls nielsen:/PROCTER',
                                     shell=True, stderr=subprocess.STDOUT)

    date_files = [str(f).strip() for f in str(output.decode(
        "utf-8")).split('\n') if len(f) > 4 and f[-4:].lower() == '.zip']
    return date_files


def get_file(filename):
    """
    Downloads a specific file from FTP and saves it locally to a folder named as the hash of the filename

    returns: temporary folder name where file was downloaded
    """

    hashed_filename = hashlib.md5(filename.encode()).hexdigest()
    download_path = global_download_path + hashed_filename

    if not os.path.exists(download_path):
        os.makedirs(download_path)

    command = rclone_binary_path + \
        ' copy nielsen:/PROCTER/{} {} -c'.format(filename, download_path)
    hf.debug('    Getting file: ' + filename, level=2)
    hf.debug('        with command:' + command, level=3)

    if args.interactive:
        input('\nPress any key to continue or ctrl-c to cancel>')

    output = subprocess.check_output(
        command, shell=True, stderr=subprocess.STDOUT)

    return download_path


def uncompress_file(file_location, filename):
    command = unzip_binary_path + \
        " -o {}/{} -d {}".format(file_location, filename, file_location)
    hf.debug('    Uncompressing file...', level=2)
    hf.debug('        with command: ' + command, level=3)

    output = subprocess.check_output(
        command, shell=True, stderr=subprocess.STDOUT)

    return output


def rename_upload_delete_file(file_location, filename):
    # zip filename is the same as the folder it contains (case-sensitive)
    zip_folder_name = filename[:-4]

    # filename : destination folder
    files_destinations = {
        'Data_File_V3_D.txt': 'datafile',
        'Campaign_Reference_File.txt': 'campaignfile',
        'Reference_File.txt': 'referencefile'
    }

    for file in files_destinations.keys():
        oldname = "/".join([file_location, zip_folder_name, file])

        newname = "/".join([file_location, zip_folder_name,
                            zip_folder_name + '_' + file])
        if not os.path.isfile(oldname):
            print(
                'Error: file {} does not exist. Continuing with next files.'.format(oldname))
            continue

        os.rename(oldname, newname)

        command = rclone_binary_path + " copy {} s3env:procter-gamble-prod/nielsendardaily/{} -c".format(
            newname, files_destinations[file]
        )
        hf.debug('    Copying to S3', level=2)
        hf.debug('        with command:' + command, level=3)

        output = subprocess.check_output(
            command, shell=True, stderr=subprocess.STDOUT)

    command = rclone_binary_path + " copy {} s3env:procter-gamble-prod/nielsendardaily/sourcefiles -c".format(
        "/".join([file_location, filename]))

    hf.debug('    Copying to S3', level=2)
    hf.debug('        with command:' + command, level=3)

    if args.interactive:
        input('? (ctrl-c to cancel)')
    output = subprocess.check_output(
        command, shell=True, stderr=subprocess.STDOUT)

    hf.debug('    Deleting temporary folder', level=2)
    shutil.rmtree(file_location)

    return True


global_download_path = "downloaded-files/"

# getting system's path of required binaries
rclone_binary_path = subprocess.check_output('which rclone', shell=True, stderr=subprocess.STDOUT).decode(
    'utf-8').strip('\n')
unzip_binary_path = subprocess.check_output('which unzip', shell=True, stderr=subprocess.STDOUT).decode('utf-8').strip(
    '\n')
aws_binary_path = subprocess.check_output(
    'which aws', shell=True, stderr=subprocess.STDOUT).decode('utf-8').strip('\n')

if not args.profile == '':
    aws_binary_path += " --profile " + args.profile

# non verbose output by default
hf.verbose = args.verbose

# bucket for original files taken from P&G sftp
# (used to check if file has already been transferred)
destination_bucket = "procter-gamble-prod"
destination_bucket_path = "nielsendardaily/sourcefiles"
destination_bucket_source_files = "procter-gamble-prod/nielsendardaily/sourcefiles"

if "" in (rclone_binary_path, unzip_binary_path, aws_binary_path):
    print("Error, at least one of required binaries not found")
    print(binaries_info())

hf.debug(binaries_info(), level=2)

files = get_file_list()

hf.debug('Starting to check already transferred files...')
for size_file in files:
    size, file = size_file.split(" ")
    # check if file exists in S3
    # command = aws_binary_path + ' s3 ls s3://{}/{} || true'.format(destination_bucket_source_files, file)
    command = aws_binary_path + ' s3api head-object --bucket {} --key {}/{} || true'.format(
        destination_bucket, destination_bucket_path, file)
    hf.debug("- Checking if filename exists in S3 sourcefiles", level=2)
    hf.debug('      with Command: `{}`'.format(command), level=3)
    try:
        output = subprocess.check_output(
            command, shell=True, stderr=subprocess.PIPE)
        hf.debug('. ', level=2)
        with open('/tmp/nielsen.out', 'w') as fh:
            # resp = json.loads(output.decode())
            resp = json.loads(output.decode())
            # fh.write(json.dumps(resp))
            fh.write("{} - {}".format(size, str(resp["ContentLength"])))
            # fh.write(json.dumps(resp, indent=2))
        if size == str(resp["ContentLength"]):
            hf.debug("    Skipping file {} because it already exists in {} and ContentLength is the same.".format(
                file,
                "s3://" + destination_bucket_source_files
            ), level=2)
            hf.debug('. ')
            continue
        print("File sizes differ ({}, ftp!=s3): {} != {}".format(
            file, size, str(resp["ContentLength"])))
    except:
        hf.debug("Unexpected error: {}".format(sys.exc_info()[0]), level=2)
        hf.debug('    It can mean the file does not exist in S3', level=2)
        hf.debug('       with command: ' + command, level=3)
        # hf.debug('    Processing file...')

    file_location = get_file(file)
    uncompress_file(file_location, file)
    rename_upload_delete_file(file_location, file)

    # break
