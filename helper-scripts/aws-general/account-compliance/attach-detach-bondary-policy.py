"""attach and detach boundary policy"""

import boto3
import sys

from compliance_checks import AssumableRole

assumable_roles = [ AssumableRole(
                        role_name="admin/ann04-sandbox-admin",
                        account_id="091021251638",
                        config_profile_fname='~/.aws/config'
                    )]
policy_arn = 'arn:aws:iam::091021251638:policy/admin/AccountBoundaryPolicy'


def get_attached_entities(policy_resource):


    entities = {
        # 'attached_groups': policy_resource.attached_groups.all(),
        'attached_roles':  policy_resource.attached_roles.all(),
        'attached_users':  policy_resource.attached_users.all(),
    }

    for attached_entities_type in entities.keys():
        print(f'Getting {attached_entities_type}')
        with open(f'{policy_resource.policy_name}-{attached_entities_type}.txt','x+') as fp:
            for member in entities[attached_entities_type]:
                print(member.name, file=fp)

    print('end')

def attach_policy_to_entities(policy_client, policy_name):
    entity_types = [
        # 'attached_groups',
        'attached_roles',
        'attached_users',
    ]

    for et in entity_types:
        with open(f'{policy_name}-{et}.txt') as fp:
            entities = fp.read().split()

        for entity_name in entities:
            # if et == 'attached_groups':
            #     policy_resource.attach_group(
            #         GroupName=entity_name
            #     )
            if et == 'attached_roles':
                policy_client.put_role_permissions_boundary(
                    RoleName=entity_name,
                    PermissionsBoundary=policy_name,
                )
            elif et == 'attached_users':
                policy_client.put_user_permissions_boundary(
                    UserName=entity_name,
                    PermissionsBoundary=policy_name,
                )

            print(f'Attached {policy_name} to {entity_name}')
    print('end')

def detach_policy_from_entities(policy_resource):
    entity_types = [
        # 'attached_groups',
        'attached_roles',
        'attached_users',
    ]

    for et in entity_types:
        with open(f'{policy_resource.policy_name}-{et}.txt') as fp:
            entities = fp.read().split()

        for entity_name in entities:
            # if et == 'attached_groups':
            #     policy_resource.detach_group(
            #         GroupName=entity_name
            #     )
            if et == 'attached_roles':
                policy_resource.detach_role(
                    RoleName=entity_name
                )
            elif et == 'attached_deers':
                policy_resource.detach_role(
                    UserName=entity_name
                )

            print(f'Detached {policy_resource.policy_name} to {entity_name}')

    print('end')


if __name__ == "__main__":
    for role in assumable_roles:
        role.get_boto3_session()

        # log_entities_attached_to_policy('AccountBoundaryPolicy')
        iam = role.session.resource('iam')
        policy_client = role.session.client('iam')
        policy = iam.Policy(policy_arn)

        get_attached_entities(policy)
        # detach_policy_from_entities(policy)
        # attach_policy_to_entities(policy_client, policy.policy_name)
