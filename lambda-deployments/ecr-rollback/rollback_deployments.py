import pylect_infra

def rollback_deployments(event):
    """ rollbacks a deployment

    Arguments:
        :event: object containing keys
            {
                "environment": string. environment being rolled back, e.g. develop,stg...,
                "app_name": string. application name e.g. annalect-docs, omni_brief,
                "num_deployments": string or int. number of ECR images to roll back. defaults to 1.
            }
    """

    print(
        f'Rolling back {event.get("num_deployments")} deployments from '
        f'{event.get(" app_name ")}-{event.get(" environment ")}'
    )

    pylect_infra.ecs.rollback_deployment(
        environment=event.get("environment"),
        app_name=event.get("app_name"),
        num_deployments=event.get("num_deployments")
    )

    return "rollback_deployment called without errors!"