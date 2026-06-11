""" Writes CSV file with the security groups """

import argparse
import sys

try:
    from tqdm import tqdm
    import pandas as pd
except:
    print('Please install tqdm: pip3 install tqdm pandas')
    sys.exit(1)
import boto3
import json
#from pprint import pprint
import re

ec2 = boto3.client('ec2')

class Script():
    ECS_INSTANCES = []

    def get_args(self):
        parser = argparse.ArgumentParser(description='Description')

        # parser.add_argument("-n", "--name", default=None,
        #                 help="Name of ...")

        parser.add_argument("-d", "--debug_options", action='store_true',
                        help="Debug options passed and exit")

        args = parser.parse_args()

        # if not any(vars(args).values()):
        #     parser.parse_args(['--help'])
        #     # parser.error('No arguments provided.')

        if args.debug_options:
            print(args)
            sys.exit()

        return args

    def get_instances(self,security_group_id):
        """returns list of instances that have the security group id"""

        ec2s = []
        for instance in self.ECS_INSTANCES:
            sgs = [sg["GroupId"] for sg in instance["SecurityGroups"]]
            if security_group_id in sgs:
                ec2s.append(instance.get('InstanceId'))

        return ec2s

    def get_groups_dictionary(self,group):
        """ Returns sg dictionary"""

        group_dict = {}

        group_dict["Name"] = group.get("GroupName")
        group_dict["Description"] = group.get("Description")
        group_dict["GroupId"] = group.get("GroupId")
        group_dict["OwnerId"] = group.get("OwnerId")

        group_dict["ingress-num-rules"] = len(group.get("IpPermissions"))
        group_dict["ingress-rules"] = json.dumps(group.get("IpPermissions"), indent=4, default=str)
        group_dict["egress-num-rules"] = len(group.get("IpPermissionsEgress"))
        group_dict["egress-rules"] = json.dumps(group.get("IpPermissionsEgress"), indent=4, default=str)

        if re.search('(wipro)|(coc)|(default)', group_dict["Name"], re.IGNORECASE):
            group_dict["wipro,coc,default"] = "*"
            group_dict["usage-in-instances"] = self.get_instances(security_group_id=group_dict["GroupId"])

        group_dict["Tags"] = None
        if group.get("Tags"):
            group_dict["Tags"] = "\n".join([f"{t['Key']}: {t['Value']}" for t in group.get("Tags")])

        return group_dict

    def get_groups(self):
        """ Returns sg list """



        group_list = []
        next_token = None
        params = {}

        while True:
            print('.', end="")
            if next_token:
                params['NextToken'] = next_token

            groups = ec2.describe_security_groups()

            group_list.extend(groups['SecurityGroups'])

            if groups.get("NextToken"):
                next_token = groups.get("NextToken")
                continue

            break
        print(f" {len(group_list)} groups found")


        return group_list

    def get_ec2s(self):
        """ get all ec2 instances

        return list of dictionaries with all instances
        """

        ec2s = []
        params = {}
        print(f"Looking for instances", end="")
        while True:
            print('.', end="")
            response = ec2.describe_instances(**params)

            for reservations in response.get('Reservations'):
                if "Instances" in reservations:
                    ec2s.extend(reservations['Instances'])

            if response.get('NextToken'):
                params['NextToken'] = response.get('NextToken')
                continue

            break

        print(f"{len(ec2s)} instances found")

        return ec2s

    def main(self):
        """Writes csv of sg descriptions"""

        descriptions = []

        self.ECS_INSTANCES = self.get_ec2s()

        print('Fetching sg ', end="")
        groups = self.get_groups()
        for group in tqdm(groups):
            descriptions.append(self.get_groups_dictionary(group))
        print("Done!")

        fname = 'security-groups.csv'
        print(f'Writing {fname}')
        df = pd.DataFrame(descriptions)
        df.to_csv(fname, index=False)
        print('Done!')





if __name__ == "__main__":
    script = Script()

    args = script.get_args()
    script.main()