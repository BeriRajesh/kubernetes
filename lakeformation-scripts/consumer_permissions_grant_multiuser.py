import boto3
import sys
import pandas as pd

# python consumer_permissions_grant.py 732327056170 fbspina_l3_reportbuilder lf-admin '/Users/firstname.lastname/Downloads/Facebook Data Science Query Access GUID Mapping.xlsx'
# python consumer_permissions_grant.py ${producer_account_no} ${database_name} ${lf-admin} ${local file location}
# import pandas as pd
table_catalog_id = sys.argv[1]
database_name = sys.argv[2]
profile_name = sys.argv[3]
excel_file = sys.argv[4]
xls  = pd.ExcelFile(excel_file)
df = pd.read_excel(xls, 'User-GUID Mapping')
df2 = df[['User Email Address', 'Omni Client GUID']].dropna().values.tolist()

# boto3.setup_default_session(profile_name='ann04-sandbox-poweruser')
# df = wr.s3.read_excel('s3://ann-iceberg-test/test/test_awswrangler_excel.xlsx',sheet_name='players')
df2 = df[['User Email Address', 'Omni Client GUID']].dropna().values.tolist()

for each_user in df2:

    analyst_arn = f"arn:aws:iam::661095214357:saml-provider/athena-lakeformation-okta:user/{each_user[0]}"
    client_id = each_user[1]

    print("boto3_version")
    print(boto3.__version__)

    session = boto3.session.Session(profile_name=profile_name, region_name='us-east-1')
    lakeformation = session.client('lakeformation')
    glue = session.client('glue')

    ########## checking and creating a database resource link ##########
    response = glue.get_databases()
    dblist = response['DatabaseList']

    resource_link_not_exists = True

    for i in range(len(dblist)):
        if dblist[i]['Name']==database_name:
            try:       
                if dblist[i]['TargetDatabase']:
                    resource_link_not_exists = False
                    print(f"resource_link {database_name} exists")
            except:
                print(f"resource_link {database_name} does not exists")

    if resource_link_not_exists:
        response_create = glue.create_database(
                            DatabaseInput={
                                'Name': database_name,
                                'TargetDatabase': {
                                    'CatalogId': table_catalog_id,
                                    'DatabaseName': database_name
                                }
                            }
                        )
        print(f"resource_link {database_name} created")

    ########## checking and creating data filter ##########
    response_dcf = lakeformation.list_data_cells_filter()

    datacellfilter_list = response_dcf['DataCellsFilters']

    dcf_not_exists = True
    template_names = ['campaign_insights', 'creative_insights', 'adset_reach_insights']
    for template_name in template_names:
        if not any(d['Name'] == f'{template_name}_{client_id}' for d in datacellfilter_list):
            print(f"Data Cell Filter {template_name}_{client_id} does not exists")
        else:
            dcf_not_exists = False
            print(f"Data cell filter {template_name}_{client_id} exists")

        if dcf_not_exists:
            create_data_filter = lakeformation.create_data_cells_filter(
                        TableData={
                            'TableCatalogId': table_catalog_id,
                            'DatabaseName': database_name,
                            'TableName': template_name,
                            'Name': f"{template_name}_{client_id}",
                            'RowFilter': {
                                'FilterExpression': f"client_id='{client_id}'"
                            },
                            'ColumnNames': [],
                            'ColumnWildcard': {
                                'ExcludedColumnNames': []
                            }
                        }
                    )
            print(f"data filter {template_name}_{client_id} created")

        ########## Resource link access to the SAML user ###########
        resource_link_grant_access = lakeformation.grant_permissions(
            Principal={
                'DataLakePrincipalIdentifier': 'IAM_ALLOWED_PRINCIPALS'
            },
            Resource={
                'Database': {
                    'Name': database_name
                }
            },
            Permissions=['ALL']
        )

        resource_link_revoke_access = lakeformation.revoke_permissions(
            Principal={
                'DataLakePrincipalIdentifier': 'IAM_ALLOWED_PRINCIPALS'
            },
            Resource={
                'Database': {
                    'Name': database_name
                }
            },
            Permissions=['ALL']
        )

        resource_link_grant_access = lakeformation.grant_permissions(
            Principal={
                'DataLakePrincipalIdentifier': analyst_arn
            },
            Resource={
                'Database': {
                    'Name': database_name
                }
            },
            Permissions=['DESCRIBE']
        )
        print(f"Granted resource link {database_name} access to {analyst_arn}")


        ########## data filter access to the analyst ##########
        data_filter_access = lakeformation.grant_permissions(
            Principal={
                'DataLakePrincipalIdentifier': analyst_arn
            },
            Resource={
                'DataCellsFilter': {
                    'TableCatalogId': table_catalog_id,
                    'DatabaseName': database_name,
                    'TableName': template_name,
                    'Name': f"{template_name}_{client_id}"
                }
            },
            Permissions=['SELECT','DESCRIBE']
        )

        print(f"granted data filter {template_name}_{client_id} access to {analyst_arn}")
