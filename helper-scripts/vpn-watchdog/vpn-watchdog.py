"""
Checks client vpn connections,
If transferred bytes < TRANSFER_THRESHOLD_BYTES then the vpn-client-connection is terminated
"""

import json
import boto3
import os
import time
import datetime
import dateutil
import traceback

def get_from_backend(fname):
    """ read file from backend """

    if BACKEND_TYPE == 'local':
        if not os.path.exists(fname):
            return None

        with open(fname) as fp:
            return json.load(fp)

    elif BACKEND_TYPE == 's3':
        try:
            response = s3.get_object(
                Bucket=BUCKET_NAME,
                Key=fname,
            )
            return json.loads(response.get('Body').read())
        except Exception as err:
            if err.response.get('Error').get('Code') == "NoSuchKey":
                return None


def dump_to_backend(data, fname):
    """ writes file to backend (S3/local) """

    if BACKEND_TYPE == 'local':
        with open(fname, 'w') as fp:
            return json.dump(data, fp)
    elif BACKEND_TYPE == 's3':
        s3.put_object(
            Body=bytes(json.dumps(data), 'utf8'),
            Bucket=BUCKET_NAME,
            Key=fname,
        )

def get_connections():

    client_vpn_endpoints = ec2.describe_client_vpn_endpoints()

    connections = []
    for client_vpn_endpoint in client_vpn_endpoints['ClientVpnEndpoints']:
        ClientVpnEndpointId = client_vpn_endpoint.get('ClientVpnEndpointId')

        params = dict(
            ClientVpnEndpointId=ClientVpnEndpointId
        )
        NextToken = ''
        while NextToken is not None:

            if NextToken:
                params['NextToken'] = NextToken

            response = ec2.describe_client_vpn_connections(**params)
            connections += response['Connections']

            NextToken = response.get('NextToken')

    active_connections = []
    for connection in connections:
        if connection['Status']['Code'] == 'active':
            active_connections.append(connection)

    # print(json.dumps(connections, indent=4, default = str))
    return active_connections

def disconnect_connection(current_connection):
    """ disconnects a connection_id """

    attempts = 3
    while attempts > 0:
        attempts -= 1
        response = ec2.terminate_client_vpn_connections(
            ClientVpnEndpointId=current_connection['ClientVpnEndpointId'],
            ConnectionId=current_connection['ConnectionId'],
        )
        try:
            connection_status = ec2.describe_client_vpn_connections(
                ClientVpnEndpointId=current_connection['ClientVpnEndpointId'],
                Filters=[{
                    "Name": "connection-id",
                    "Values": [current_connection['ConnectionId']],
                }],
            )
            if connection_status['Connections'][0]['Status']['Code'] == 'terminated':
                print(f"{current_connection['Username']}'s client vpn connection terminated!")
                return
        except Exception as error:
            if error.response['Error']['Code'] == 'InvalidVpnConnectionID.NotFound':
                print(f"{current_connection['Username']}'s client vpn connection connection not found anymore!")
                break
            traceback.print_exc()

        print(f"{current_connection['Username']}'s couldn't be terminated! Trying {attempts} more times ...")
        time.sleep(3)

def check_bytes_transferred():
    """ checks bytes transferred for each connected user comparing from the backend """

    # print("load old connections")
    old_connections = get_from_backend(CONNECTIONS_FNAME)

    # print("getting connections")
    current_connections = get_connections()

    # print("writing current connections")
    dump_to_backend(current_connections, CONNECTIONS_FNAME)

    if not old_connections:
        print('No old connections')
        return

    # print("comparing connections times")
    old_connections_map = {}
    for old_connection in old_connections:
        connection_id = old_connection.get('ConnectionId')
        old_connections_map[connection_id] = old_connection


    for current_connection in current_connections:
        connection_id = current_connection.get('ConnectionId')
        if connection_id not in old_connections_map:
            continue

        connection_timestamp = dateutil.parser.parse(current_connection['Timestamp'])
        connection_established = dateutil.parser.parse(current_connection['ConnectionEstablishedTime'])

        old_connection = old_connections_map.get(connection_id)
        username = current_connection.get("Username")

        if connection_timestamp - connection_established < datetime.timedelta(seconds=LOOPTIME_SECONDS):
            print(f"{username}'s connection less than {LOOPTIME_SECONDS}s")
            continue

        bytes_ingress = int(current_connection.get('IngressBytes')) - int(old_connection.get('IngressBytes'))
        bytes_egress = int(current_connection.get('EgressBytes')) - int(old_connection.get('EgressBytes'))

        total_bytes_transferred = bytes_ingress + bytes_egress
        if bytes_ingress + bytes_egress < TRANSFER_THRESHOLD_BYTES:
            print(f'User {username} has transferred {total_bytes_transferred} bytes since last check and is being disconnected.')
            print(json.dumps(current_connection, indent=4))
            if "anmichel" in username:
                disconnect_connection(current_connection)

        else:
            print(f'User {username} has transferred {total_bytes_transferred} bytes since last check. Connection seems active.')

def main(loop=False):
    """ main loop """

    while True:
        print(f'---- {datetime.datetime.now()} ---')
        check_bytes_transferred()
        if not loop:
            break
        time.sleep(LOOPTIME_SECONDS)


if __name__ == "__main__":
    s3 = boto3.client('s3')
    ec2 = boto3.client('ec2')

    BACKEND_TYPE = "s3"
    BUCKET_NAME = "adt-automation"
    CONNECTIONS_FNAME = "vpn/client-vpn-connections.json"

    LOOPTIME_SECONDS = os.environ.get('LOOPTIME_SECONDS') or 60*60 # default 1h
    TRANSFER_THRESHOLD_BYTES = os.environ.get('LOOPTIME_SECONDS') or 3_600_000 # default 3.6Mb

    LOOPTIME_SECONDS= int(LOOPTIME_SECONDS)
    TRANSFER_THRESHOLD_BYTES= int(TRANSFER_THRESHOLD_BYTES)


    main(loop=False)


