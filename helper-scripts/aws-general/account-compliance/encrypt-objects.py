"""Encrypt objects in a bucket by copying each object onto itself"""

import datetime
import json
import subprocess
import sys
import os

import compliance_checks
from compliance_checks import AssumableRole

# only encrypt buckets on these account
only_accounts_dict = {
    #utility1
    'utility1': [
        # '348194362585',

        #2nd round
        '408764662748',
        '153175995455',
        '288489547540',
        '895757120061',
        '175813369871',
        '366146577560',
        # '345951534139',
    ],

    #utility 2
    'utility2': [
        '952850296487',
        '091021251638',
        '571875174059',
        '431361936815',
        '914006819694',
        '661095214357',
        '732327056170',
    ],

    'utility3': [
        '005533607590'
    ],

    'utility4': [
        '340659147180'
    ],

    'utility5': [
        '345951534139'
    ],

}

only_accounts = []

# ignore this account from process
ignore_accounts = [
    # "091021251638",
    # "571875174059",
    # "661095214357",
    # "732327056170",
    # "914006819694",
    # "952850296487",
    # "431361936815",

    # instance per account (mostly)

]

ignore_buckets = [
    # utility1
    "accuen-test-01",
    "accuenplatform-adhoc-dev",
    "accuenplatform-adhoc-prod",
    "accuenplatform-changelogs",
    "accuenplatform-dt-drop",
    "accuenplatform-public",
    "accuenplatform-reports",

    # utility1 # 220815
    'accuen-drop'
    'accuenplatform-adhoc-devsri'
    'annalect-annalect-omniscope-dev'
    'com.accuenplatform.async_reports'
    'com.accuenplatform.emr.tempredshifttohive'
    'com.annalect.files.uploads.dc-facebook-admin-prod'
    'com.annalect.files.uploads.dc-facebook-admin-test'
    'com.annalect.files.uploads.google-coda-app-test'
    'com.annalect.files.website.dc-facebook-admin-prod'
    'com.annalect.files.website.google-coda-app-test'
    'l1-digitalcontent-acxiom-temp'


    # nohup.out.220803 # utility1
    'accuenplatform-stage',
    'accuenplatform.com',
    'amc-omgbeiersdorfaquaphorbabyus-vqv5dsqe',
    'amc-omgbeiersdorfaquaphorhblus-86qgh8vv',
    'amc-omgbeiersdorfeucerinus-svzcxbgv',
    'amc-omgbeiersdorfmocksus-oljgqh3u',
    'amc-omgbeiersdorfnivea-po8gctgq',
    'amc-omgbombardierrecreationalus-ztomn888',
    'amc-omgcarnivalcruiselinesus-wsfmyhzv',
    'amc-omgcignaus-bjqsekxr',
    'amc-omgcwnetworkus-gev6etlu',
    'amc-omgdolbylaboratoriesus-v4smajhv',
    'amc-omgenergyupgradecaliforniaus-qg1qbjoy',
    'amc-omgferrerous-wyfmi4of',
    'amc-omggeneralelectricus-kkl8znkk',
    'amc-omghawaiitourismus-4nxal7vb',
    'amc-omghewletpackardprintus-7kmm808f',
    'amc-omghewletpackardpsu-jtdapsrz',
    'amc-omghormelfoodulinaryus-nf0n9ka4',

    # nohup.out-220810-finished-elde # utility1
    'amc-omghormelpepperonius-ma8g6ick',
    'amc-omghsbcus-gvfwbshc',
    'amc-omgkohlercompaynus-j5wbnsbq',
    'amc-omgkraftheinzus-a3ajjayf',
    'amc-omglongchampus-bu79tlvw',
    'amc-omgmitsubishius-myjhntnj',
    'amc-omgnissantier2us-dynbwxdm',
    'amc-omgpepsicocheetosus-aliyvyqe',
    'amc-omgpepsicosunchipsus-layyzypp',
    'amc-omgprincipalfinancalgroupus-5mgzilxl',
    'amc-omgscjgladeus-ktvtxlz0',
    'amc-omgscjhomecleaningus-2kikqyvy',
    'amc-omgscjziplocus-bepqa9pn',
    'amc-omgserinocoyneus-obrfpqcj',
    'amc-omgsynchronyfinancialus-cmvxpisk',
    'amc-omgtomsus-wbc7wxpg',
    'amc-omgturnerwarnerus-hygecupx',
    'amc-omgvolkswagenus-w62la8s6',
    'annalect-annalect-omniscope',
    'automationscripts-accuen',
    'aws-athena-query-results-348194362585-us-west-2',
    'aws-cloudtrail-logs-348194362585-d872fde3',
    'aws-glue-assets-348194362585-us-west-2',
    'aws-glue-scripts-348194362585-us-west-2',
    'aws-glue-temporary-348194362585-us-west-2',
    'aws-sam-cli-managed-default-samclisourcebucket-177d7sdygcsx6',
    'aws-sam-cli-managed-default-samclisourcebucket-jri8iwcw7k2o',
    'com.accuenbi.qb',
    'com.accuenplatform.airflow.logs',
    'com.accuenplatform.cloudtrail',
    'com.accuenplatform.config',
    'com.accuenplatform.dev1.logs',
    'com.accuenplatform.fee-calculator',
    'com.accuenplatform.prod.logs',
    'com.accuenplatform.qubole',
    'com.accuenplatform.qubole',
    'com.accuenplatform.qubole',
    'com.accuenplatform.qubole',
    'com.accuenplatform.qubole',
    'com.accuenplatform.qubole',
    'com.accuenplatform.qubole',
    'com.accuenplatform.smp',
    'com.accuensmp.drop',
    'com.annalect.build.artifacts',
    'com.annalect.build.config',
    'com.annalect.files.uploads.cleanrooms-service-test',
    'com.annalect.files.website.cleanrooms-service-test',
    'com.annalect.files.website.dc-facebook-admin-test',
    'com.annalect.files.website.dc-report-builder-prod',
    'com.annalect.files.website.dc-report-builder-test',
    'com.annalect.files.website.omniscope-test',
    'com.annalect.logs.campaign-api-test',
    'com.annalect.logs.cleanrooms-service-test',
    'com.annalect.logs.dc-facebook-admin-prod',
    'com.annalect.logs.dc-facebook-admin-test',
    'com.annalect.logs.dc-report-builder-prod',
    'com.annalect.logs.dc-report-builder-test',
    'com.annalect.logs.google-coda-app-test',
    'com.annalect.logs.omniscope-test',
    'com.apis.screenshots',
    'com.jenkins-airflow-alb-logs',
    'dcdt-adhoc-reports',
    'dcdt-ttd-audience-builder',
    'dcdt-ttd-iar',
    'digitalcontent-scripts',
    'example-spa-1',
    'example-spa-2',
    'l1-digitalcontent-acxiom',
    'path-based-routing-test-1',
    'path-based-routing-test-2',
    'pixeltest.accuenplatform.com',
    'sub-spa-test',
    'airflow-logs-257841078254-eu-west-1-emea-live',

    # utility2: nohup.out-encryption-utility2-220811
    'ann01-tioprod-aue1-codebuild-cache',
    'aws-athena-query-results-us-east-1-661095214357',
    'ann02-nonprod-ads-devops',
    'Competitive',
    'UX_Creative',
    'ai-mcdonalds-backup',
    'annalect-bitbucket-backup',
    'annalect-gdproject',
    'annalectassets-alienvault-cloudtrail',
    'annalectcloudtrail-assets',
    'annalectlabs',
    'aok-rulezzz',
    'bacardi',
    'datagroup-metacenter',
    'datashaka-bacardi',
    'hulnow.annalect.com',
    'hurricane.annalect.com',
    'omdusa',
    'hurricane.annalect.com',
    'omdusa',
    'post.annalect.com',
    'programmaticcreative.annalect.com',
    'resolutionmedia',
    'rm-cleartarget',
    'sandbox-crossaccount-lakeformation-test',
    'spotifyhackathon',
    'ux-creative-backup',
    'vizio-data',
    'ux-creative-backup',
    'vizio-data',
    'wcai',
    'ann04-sandbox-athena-queryresult',
    'aws-athena-query-results-us-west-2-091021251638',
    'test-costreport-sandbox',
    'ann05-nonprod-aadl-devops',
    'aws-logs-431361936815-us-east-1',

    'aws-glue-scripts-914006819694-us-east-1',
    'aws-glue-temporary-914006819694-us-east-1',

    # utility2: 220815
    'datadog-forwarder-annalect-bucket',
    'annalect-database-backup',
    'annalect-video-thumbs',
    'config-bucket-952850296487',
    'rm-flightdeck',
    'aws-glue-scripts-914006819694-us-east-1',
    'aws-glue-temporary-914006819694-us-east-1',
    'sagemaker-studio-h1uci6b70b5',

    # utility3: 220815
    'annalect',
    'annalect-emea',
    'annalect-emea-adp-analysis',
    'annalect-emea-adp-configuration',
    'annalect-emea-adp-processed-data',
    'annalect-emea-adp-raw-data',
    'annalect-emea-adp-system-tests',
    'annalect-emea-adp-unit-tests',
    'annalect-emea-artefacts',
    'annalect-emea-aws-logs',
    'annalect-emea-billing',
    'annalect-emea-cloudtrail',

    #utility4: 220815
    'annalect-devops-gluedb-backup',
    'annalect-emea-analytics-dev',
    'annalect-emea-analytics-dev-long-life',
    'annalect-emea-analytics-dev-persist',
    'annalect-emea-dev-jupyter-notebook',
    'annalect-emea-dev-jupyterhub-deployment',
    'annalect-emea-kops-340659147180',
    'annalect-emea-lotame-temp',
    'annalect-emea-prd-ireland-database',
    'annalect-emea-prd-ireland-notebook',
    'annalect-emea-prd-italy-database',
    'annalect-emea-prd-italy-notebook',
    'annalect-emea-prd-mena-database',
    'annalect-emea-prd-mena-notebook',
    'annalect-emea-prd-omduk-database',
    'annalect-emea-prd-omduk-notebook',
    'annalect-emea-prd-omgfinland-database',
    'annalect-emea-prd-omgfinland-notebook',
    'athena-query-prd-core-ireland',
    'athena-query-prd-core-italy',
    'athena-query-prd-core-mena',
    'athena-query-prd-core-omduk',
    'athena-query-prd-core-omgfinland',
    'aws-athena-query-results-340659147180-eu-west-1',
    'aws-glue-scripts-340659147180-eu-west-1',
    'aws-glue-temporary-340659147180-eu-west-1',
    'aws-logs-340659147180-eu-west-1',
    'aws-logs-340659147180-us-east-1',
    'emr-rpms0044a84475d1e589775deecdcf',

    # utility5
    'aadl-aqfer-collab',
    'accuen.dsdk.input',
    'accuen_dsdk_input',
    'adx_data_transfer_87335458',
    'airflow-ecktest',
    'ak_redshift_queries',
    'amc-omnicomhandsattus-eb2xd4rs',
    'annalect-aqfer-terraform-state',
    'annalect-test1',
    'annalect-useast1-hs-army',
    'aud-ds-mwaa',
    'audience-datascience',
    'aws-athena-query-results-345951534139-eu-west-1',
    'aws-athena-query-results-345951534139-us-east-1',
    'aws-athena-query-results-us-east-1-345951534139',
    'aws-glue-scripts-345951534139-us-east-1',
    'aws-glue-temporary-345951534139-us-east-1',
    'aws-logs-345951534139-us-east-1',
    'aws-sam-cli-managed-default-samclisourcebucket-1tgh01dxf2cai',
    'cf-templates-1t0vnnaazed9p-us-east-1',
    'cf-templates-1t0vnnaazed9p-us-west-2',
    'cicd-workshop-us-east-1-345951534139',
    'cloud9-345951534139-sam-deployments-us-east-1',
    'codepipeline-us-east-1-378888392731',
    'com.accuen.contextualdatafeeds',
    'com.accuen_share.data',
    'com.accuenbi.aipdm',
    'com.accuenbi.ap_console',
    'com.accuenbi.ap_console.dev2',
    'com.accuenbi.ap_console.dev_test_01',
    'com.accuenbi.awslogs',
    'com.accuenbi.awslogs-query-output',
    'com.accuenbi.backups',
    'com.accuenbi.bigdata',
    'com.accuenbi.cloudtrail',
    'com.accuenbi.conf',
    'com.accuenbi.datafeeds.byoa-mediamath',
    'com.accuenbi.datafeeds.cognitiv',
    'com.accuenbi.datafeeds.comscore',
    'com.accuenbi.datafeeds.epsilon',
    'com.accuenbi.datafeeds.sambatv',
    'com.accuenbi.datafeeds.trueffect',
    'com.accuenbi.datafeeds.videology',
    'com.accuenbi.datarepo1',
    'com.accuenbi.dev',
    'com.accuenbi.doug',
    'com.accuenbi.eckamm.dev',
    'com.accuenbi.eckamm.dev.pctest1',
    'com.accuenbi.emea.adform',
    'com.accuenbi.emr',
    'com.accuenbi.eu-west-1.conf',
    'com.accuenbi.eu-west-1.dev-level-2',
    'com.accuenbi.eu-west-1.lz',
    'com.accuenbi.hersheys_freq2012',
    'com.accuenbi.info',
    'com.accuenbi.logs',
    'com.accuenbi.projects',
    'com.accuenbi.projects.bqtcache',
    'com.accuenbi.projects.dmcache',
    'com.accuenbi.projects.fedex.visualiq',
    'com.accuenbi.projects.lilly_backup',
    'com.accuenbi.projects.peer39',
    'com.accuenbi.projects.s3_logs',
    'com.accuenbi.projects.seaworld.woody',
    'com.accuenbi.qubole',
    'com.accuenbi.sf2012',
    'com.accuenbi.smp',
    'com.accuenbi.smptest',
    'com.accuenbi.stoplight',
    'com.accuenbi.tmp',
    'com.accuenbi.us-east-1.datafeeds.doubleverify',
    'com.accuenbi.us-east-1.datafeeds.flashtalking',
    'com.accuenbi.us-east-1.datafeeds.innovid',
    'com.accuenbi.us-east-1.datafeeds.mediamath',
    'com.accuenbi.us-east-1.datafeeds.moat',
    'com.accuenbi.us-east-1.datafeeds.oath',
    'com.accuenbi.us-east-1.datafeeds.sizmek',
    'com.accuenbi.us-east-1.dev-level-2',
    'com.accuenbi.us-east-1.level-0',
    'com.accuenbi.us-east-1.level-2',
    'com.accuenbi.us-east-1.lz',
    'com.accuenbi.us-east-1.sagemaker.eric-kamm',
    'com.accuenbi.us-east-1.tmp15',
    'com.accuenbi.user',
    'com.annalect.datafeeds',
    'com.annalect.us-east-1.byoa',
    'com.annalect.us-east-1.elde',
    'com.annalect.us-east-1.elde-user.eric.kamm',
    'com.annalect.videoamp.temp',
    'com.heartsandscience.us-east-1.datafeeds.ac-intuit',
    'com.heartsandscience.us-east-1.datafeeds.appnexus',
    'com.heartsandscience.us-east-1.datafeeds.doubleverify',
    'com.omd.us-east-1.datafeeds.appnexus',
    'com.omdphd.us-east-1.datafeeds.appnexus',
    'com.omg.omd.datafeeds',
    'com.omg.phd.datafeeds',
    'dev-aud-ds',
    'dev-audience-data',
    'edc-test',
    'esq-useast1-phd-casper',
    'eu-west-1.accuenbi.tmp',
    'from-aqfer-poc',
    'mwaa-s3-check-access',
    'mwaa-s3-check-access-1',
    'test-a-datascience',
    'test-bucket-chandran-west',
    'test-elde-mwaa',
    'trycdkstack-myfirstbucketb8884501-182m1gehk5uiu',
    'useast-datafeeds-juul-5371a9036784',
    'useast1-auds-level1',
    'useast1-auds-level1-archive',
    'useast1-auds-level2',
    'useast1-datafeeds-icon-ashley-flashtalking',


]

assumable_roles = [
    assumable_role for assumable_role in compliance_checks.assumable_roles
    if assumable_role.account_id not in ignore_accounts
]


def load_log(fname: str) -> list[dict]:
    """Returns contents of fname as a list of dict"""

    with open(fname) as fp:
        lines = fp.read().split('\n')

    return [json.loads(line) for line in lines if line]


def encrypt_bucket_contents(bucket_name: str, role: AssumableRole) -> None:
    """Encrypts all objects in bucket_name by copying them unto themselves, using aws s3 cp ... ... --recursive --sse """

    cmd = f'aws --{role.profile_name} s3 cp --no-progress s3://{bucket_name}/ s3://{bucket_name}/ --sse --recursive'
    print(
        f"""\n\n\n
        **************************
        Encrypting {bucket_name=}
        command: {cmd}
        account_id: {role.account_id}
        datetime: {datetime.datetime.now()}
        \n\n""")

    # running with subprocess.Popoen so we can monitor the continuous output
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=3000, shell=True)
    for line in iter(p.stdout.readline, b''):
        print(line)
    p.stdout.close()
    p.wait()


def log_action(value: dict, log_type: str = "action_log") -> None:
    """Logs value to file"""

    value['timestamp'] = str(datetime.datetime.now())
    with open(f'{log_type}.log', 'a') as fp:
        json.dump(value, fp=fp, sort_keys=True, default=str)
        print(file=fp)

    print(value)


def get_encrypt_buckets(
    actions_taken: list[dict],
    only_accounts: list[str] | None = None,
    only_accounts_dict: dict[str, list[str]] | None = None,
    ignore_accounts: list[str] | None = None,
    ignore_buckets: list[str] | None = None) -> dict:
    """Return dictionary of type account_id: list of buckets whose contents need to be encrypted, only for accounts in only_accounts"""

    if not only_accounts:
        only_accounts = []
    if not ignore_accounts:
        ignore_accounts = []
    if not ignore_buckets:
        ignore_buckets = []
    if not only_accounts_dict:
        only_accounts_dict = {}

    encrypt_buckets: dict[str, list[str]] = {}
    for action in actions_taken:
        account_id = action['account_id']

        if only_accounts_dict:
            if os.path.isfile('whoami'):
                whoami = open('whoami').read()
                only_accounts = only_accounts_dict[whoami]

        if only_accounts and account_id not in only_accounts:
            continue

        if account_id in ignore_accounts:
            continue

        bucket_name = action['bucket_name']
        if ignore_buckets and bucket_name in ignore_buckets:
            continue

        action_performed = action['action']
        if action_performed != 'encrypted-bucket':
            continue

        if account_id not in encrypt_buckets:
            encrypt_buckets[account_id] = []

        encrypt_buckets[account_id].append(bucket_name)  # type: ignore

    return encrypt_buckets


def main() -> None:
    """Get bucket to encrypt from action_log and encrypts the contents if bucket belongs to account in only_accounts"""

    ###############
    # useful to assume all role first and save credentials

    # for role in assumable_roles:
    #     print(f'{role.account_id}', end='')
    #     role.get_boto3_session()
    #     print(f' OK')

    # sys.exit()

    ###############

    actions_taken = load_log(fname='action_log.log')

    # only encrypt buckets on these account
    encrypt_buckets = get_encrypt_buckets(
        actions_taken=actions_taken,
        only_accounts=only_accounts,
        only_accounts_dict=only_accounts_dict,
        ignore_accounts=ignore_accounts,
        ignore_buckets=ignore_buckets,
    )

    for role in assumable_roles:
        if role.account_id != '345951534139':
            continue

        role.get_boto3_session()

        if role.account_id not in encrypt_buckets:
            continue

        for bucket_name in encrypt_buckets[role.account_id]:
            encrypt_bucket_contents(bucket_name=bucket_name, role=role)


if __name__ == "__main__":
    main()
    print('end')
