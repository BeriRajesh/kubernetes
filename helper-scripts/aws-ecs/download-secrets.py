# download secrets

import subprocess
import os
import sys

envs = ['dev', 'qa', 'stg', 'prod']

secrets = [
"dev/ssowrapper/app_secrets.encrypted",
"dev/ssowrapper/dev.py.encrypted",
"annalect_batchjobs/aws_s3_credentials",
"annalect_batchjobs/prod/dsdk_file_status_error/adeuser",
"annalect_batchjobs/prod/multi_client_data_feed/dmp-reporting",
"annalect_batchjobs/prod/multi_client_data_feed/dmp-reporting/.rqt-config",
"annalect_batchjobs/prod/multi_client_data_feed/dmp-reporting/envs.sh",
"annalect_batchjobs/prod/multi_client_data_feed/dmp-reporting/ez_setup.py",
"annalect_batchjobs/prod/multi_client_data_feed/dmp-reporting/requirements.txt",
"annalect_batchjobs/prod/multi_client_data_feed/dmp-reporting/rqt-0.1.3-py2.7.egg",
"annalect_batchjobs/prod/multi_client_data_feed/ds3/.boto",
"annalect_batchjobs/prod/multi_client_data_feed/ds3/envs.sh",
"annalect_batchjobs/prod/multi_client_data_feed/ds3/id_rsa_wf_axst",
"annalect_batchjobs/prod/multi_client_data_feed/ds3/requirements.txt",
"annalect_batchjobs/prod/multi_client_data_feed/ds3/sftp.config",
"annalect_batchjobs/prod/multi_client_data_feed/ds3/Welcome-36e68710-d86a-11e8-ab2a-8c859054f815",
"annalect_batchjobs/prod/multi_client_data_feed/ds3/wellsfargo.pem",
"annalect_batchjobs/prod/multi_client_data_feed/ds3/wf_rsa_key.ppk",
"annalect_batchjobs/prod/multi_client_data_feed/dsdk_file_processing/.rqt-config",
"annalect_batchjobs/prod/multi_client_data_feed/dsdk_file_processing/envs.sh",
"annalect_batchjobs/prod/multi_client_data_feed/dsdk_file_processing/ez_setup.py",
"annalect_batchjobs/prod/multi_client_data_feed/dsdk_file_processing/rqt-0.1.3-py2.7.egg",
"annalect_batchjobs/prod/multi_client_data_feed/dsdk_file_processing/serveroverride.cfg",
"annalect_batchjobs/prod/multi_client_data_feed/dt/.boto",
"annalect_batchjobs/prod/multi_client_data_feed/dt/access_config.json",
"annalect_batchjobs/prod/multi_client_data_feed/dt/envs.sh",
"annalect_batchjobs/prod/multi_client_data_feed/dt/requirements.txt",
"annalect_batchjobs/prod/multi_client_data_feed/Welcome-fc0af58a-d7b1-11e8-ab95-8c859054f815",
"annalect_batchjobs/prod/multi_client_data_feed/wfDCM/.boto",
"annalect_batchjobs/prod/multi_client_data_feed/wfDCM/adeserver.cfg",
"annalect_batchjobs/prod/multi_client_data_feed/wfDCM/envs.sh",
"annalect_batchjobs/prod/multi_client_data_feed/wfDCM/id_rsa_wf_axst",
"annalect_batchjobs/prod/multi_client_data_feed/wfDCM/sftp.config",
"annalect_batchjobs/prod/multi_client_data_feed/wfDCM/Welcome-36e68710-d86a-11e8-ab2a-8c859054f815",
"annalect_batchjobs/prod/multi_client_data_feed/wfDCM/wellsfargo.pem",
"annalect_batchjobs/prod/multi_client_data_feed/wfDCM/wf_rsa_key.ppk",
"annalect_batchjobs/prod/pngftp2s3sync/annalect_admin",
"annalect_batchjobs/prod/rclone-adgooroo/rclone.conf",
"annalect_batchjobs/prod/rclone-sync/rclone.conf",
"annalect_batchjobs/redshift_db.cfg",
"annalect_batchjobs/secrets.txt",
"annalect_batchjobs/to_delete/",
"annalect_batchjobs/to_delete/multi_client_data_feed/Welcome-fc0af58a-d7b1-11e8-ab95-8c859054f815",
"annalect_batchjobs/to_delete/multi_client_data_feed/wfDCM/.boto",
"annalect_batchjobs/to_delete/multi_client_data_feed/wfDCM/envs.sh",
"annalect_batchjobs/to_delete/multi_client_data_feed/wfDCM/wellsfargo.pem",
"annalect_batchjobs/to_delete/multi_client_data_feed/wfDCM/wf_rsa_key.ppk",
"database/redshift_db.cfg",
"dev/ade/adeserveroverride.cfg.encrypted",
"dev/ade/get_app_secrets.encrypted",
"dev/adeingest/adeserveroverride.cfg",
"dev/adeweb/adeserveroverride.cfg",
"dev/annalect-docs/serveroverride.cfg.encrypted",
"dev/aubi/credentials.ini.encrypted",
"dev/aubi/serverbase.cfg.encrypted",
"dev/aubi/serveroverride.cfg.encrypted",
"dev/audience_emea/serveroverride.cfg.encrypted",
"dev/audiencebuilder/serveroverride.cfg.encrypted",
"dev/audiencebuilderui/serveroverride.cfg.encrypted",
"dev/b2bcontent/serveroverride.cfg.encrypted",
"dev/b2binsights/serveroverride.cfg.encrypted",
"dev/bacardisceplan/serveroverride.cfg.encrypted",
"dev/cardboard/serveroverride.cfg.encrypted",
"dev/civ2computing/serveroverride.cfg.encrypted",
"dev/dswebutil/serveroverride.cfg.encrypted",
"dev/inspiration-src/serveroverride.cfg.encrypted",
"dev/inspiration/serveroverride.cfg.encrypted",
"dev/journey_src/serveroverride.cfg.encrypted",
"dev/journeyss/serveroverride.cfg.encrypted",
"dev/modelbuilder/serveroverride.cfg.encrypted",
"dev/nissansceplan/serveroverride.cfg.encrypted",
"dev/omni-scheduler/serveroverride.cfg.encrypted",
"dev/omni/serveroverride.cfg.encrypted",
"dev/omnibrief/serveroverride.cfg.encrypted",
"dev/omniui/serveroverride.cfg.encrypted",
"dev/pathway/serveroverride.cfg.encrypted",
"dev/portal/get_app_secrets.encrypted",
"dev/portal/serverbase.cfg.encrypted",
"dev/portal/serveroverride.cfg.encrypted",
"dev/portalui/serveroverride.cfg.encrypted",
"prod/ade/adeserveroverride.cfg.encrypted",
"prod/adeingest/adeserveroverride.cfg",
"prod/adeweb/adeserveroverride.cfg",
"prod/airflow/app_secrets.encrypted",
"prod/airflow/serveroverride.cfg.encrypted",
"prod/annalect-docs/serveroverride.cfg.encrypted",
"prod/annalect-tech/serveroverride.cfg.encrypted",
"prod/audience_emea/serveroverride.cfg.encrypted",
"prod/audiencebuilder/serveroverride.cfg.encrypted",
"prod/b2bcontent/serveroverride.cfg.encrypted",
"prod/b2binsights/serveroverride.cfg.encrypted",
"prod/bacardisceplan/serveroverride.cfg.encrypted",
"prod/cardboard/serveroverride.cfg.encrypted",
"prod/dswebutil/serveroverride.cfg.encrypted",
"prod/fbconnect/serveroverride.cfg.encrypted",
"prod/inspiration-src/serveroverride.cfg.encrypted",
"prod/inspiration/serveroverride.cfg.encrypted",
"prod/journey_audience_builder/serveroverride.cfg.encrypted",
"prod/journey_src/serveroverride.cfg.encrypted",
"prod/journeyss/serveroverride.cfg.encrypted",
"prod/modelbuilder/serveroverride.cfg.encrypted",
"prod/multi_client_data_feed/serveroverride.cfg.encrypted",
"prod/nissansceplan/serveroverride.cfg.encrypted",
"prod/omni-scheduler-eu/serveroverride.cfg.encrypted",
"prod/omni-scheduler/serveroverride.cfg.encrypted",
"prod/omni/serveroverride.cfg.encrypted",
"prod/omnibrief/serveroverride.cfg.encrypted",
"prod/pathway/serveroverride.cfg.encrypted",
"prod/portal/get_app_secrets.encrypted",
"prod/portal/serveroverride.cfg.encrypted",
"prod/ssowrapper/app_secrets.encrypted",
"prod/ssowrapper/prod.py.encrypted",
"qa/ade/adeserveroverride.cfg.encrypted",
"qa/adeingest/adeserveroverride.cfg",
"qa/adeweb/adeserveroverride.cfg",
"qa/annalect-docs/serveroverride.cfg.encrypted",
"qa/audience_emea/serveroverride.cfg.encrypted",
"qa/audiencebuilder/serveroverride.cfg.encrypted",
"qa/b2bcontent/serveroverride.cfg.encrypted",
"qa/b2binsights/serveroverride.cfg.encrypted",
"qa/cardboard/serveroverride.cfg.encrypted",
"qa/inspiration-src/serveroverride.cfg.encrypted",
"qa/inspiration/serveroverride.cfg.encrypted",
"qa/omni-scheduler/serveroverride.cfg.encrypted",
"qa/omni/serveroverride.cfg.encrypted",
"qa/omnibrief/serveroverride.cfg.encrypted",
"qa/pathway/serveroverride.cfg.encrypted",
"qa/ssowrapper/app_secrets.encrypted",
"qa/ssowrapper/qa.py.encrypted",
"stg/audiencebuilder/serveroverride.cfg.encrypted",
"stg/b2bcontent/serveroverride.cfg.encrypted",
"stg/b2binsights/serveroverride.cfg.encrypted",
"stg/cardboard/serveroverride.cfg.encrypted",
"stg/inspiration-src/serveroverride.cfg.encrypted",
"stg/inspiration/serveroverride.cfg.encrypted",
"stg/omni-scheduler/serveroverride.cfg.encrypted",
"stg/omni/serveroverride.cfg.encrypted",
"stg/omnibrief/serveroverride.cfg.encrypted",
]

for secret in secrets:
    try:
        env, app, *file = secret.split("/")
        fileparts = secret.split("/")
    except Exception as e:
        print(f"{e}: {secret}")
        continue

    if len(sys.argv) > 0 and sys.argv[1] != env:
        continue

    if len(sys.argv) > 1 and sys.argv[2] != app:
        continue

    try:
        if file[-1].split('.')[-1] != 'encrypted':
            print(f"Skipping {secret}")
            continue
    except:
        print(f"Skipping {secret}")
        continue

    secretsfile = ".".join(fileparts[-1].split('.')[0:-1])
    print(f"file: {secretsfile}")

    if env in envs:
        print(f"Environment: {env},",end="")
        print(f"App: {app},")
    else:
        continue

    if app[0:3] == "ade" and app != "ade":
        print(f"Skipping {app}")
        continue

    try:
        out = subprocess.check_output(f'./download_docker_secrets.sh --file={secretsfile} --QUIET=" " --force=true --env={env} --app={app}', shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise RuntimeError("command '{}' return with error (code {}): {}".format(e.cmd, e.returncode, e.output))
    print(out.decode())

    filename = subprocess.check_output(f'\\ls -rt -1 | tail -n 1', shell=True, stderr=subprocess.STDOUT)
    filename = filename.decode().strip()


    print(f"downloaded file {filename}")

    secrets_path = "./secrets"
    if not os.path.exists(secrets_path):
        os.mkdir(secrets_path)

    os.rename(filename, f"secrets/{app}-{env}-{filename}")

print('All files downloaded in secrets/')


    # if env == "annalect_batchjobs":
    #     env = app
    #     if len(file) == 0:
    #         continue
    #     app = file[0]
    #     print(f"AnnalectBatchJobs-",end="")
    #     print(f"Environment: {env}",end="")
    #     print(f"App: {app}")

