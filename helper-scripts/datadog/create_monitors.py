#!/usr/bin/env python3

"""Create datadog monitors"""
import argparse
import sys

# sys.path.append('../')
# import lib.helper_functions as hf

import datadog
import copy

from pprint import pprint
import os

import sys
import textwrap

# sys.path.append('../')
# import lib.helper_functions as hf

def dict_merge(dct, merge_dct):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    :return: None

    taken from: https://gist.github.com/angstwad/bf22d1822c38a92ec0a9
    (adapted to Python3)
    """
        # pprint(dct)
        # pprint(merge_dct)
    for k, v in merge_dct.items():
        # print(k)
        if k in dct and isinstance(dct[k], dict) and isinstance(merge_dct[k], dict):
            # print('rec')
            # pprint(dct[k])
            # pprint(merge_dct[k])
            dict_merge(dct[k], merge_dct[k])
        else:
            # print('lin')
            dct[k] = merge_dct[k]

        # pprint(dct[k])
        # pprint(merge_dct[k])

parser = argparse.ArgumentParser(description='Export resources from AWS')

args = parser.parse_args()

if "DD_API_KEY" not in os.environ or "DD_APP_KEY" not in os.environ == "":
    sys.exit("ERROR: Environment variables DD_API_KEY and/or DD_APP_KEY must be set to continue.")

# reading datadog keys from environment
options = {
    'api_key': os.environ['DD_API_KEY'],
    'app_key': os.environ['DD_APP_KEY']
}
# strip() necessary in some systems that return the variable with a "\r"
options = {k: v.strip() for k, v in options.items()}
datadog.initialize(**options)

# notification destinations
critical_alerts_notifications = "@teams-Datadogalerts @slack-alerts-critical @devops@annalect.com"
high_alerts_notifications = "@teams-Datadogalerts @slack-alerts-high @devops@annalect.com"
recovery_notifications = "@teams-Datadogalerts @slack-notifications-dd"

all_monitors = datadog.api.Monitor.get_all()

# environments
PRODUCTION = 'prod'
DEVELOPMENT = 'dev'
QA = 'qa'
MANAGEMENT = 'mgmt'


def get_monitor_id(name):
    """ returns the id of a monitor by name, for monitors with adt-script tag """
    for monitor in all_monitors:
        if name == monitor['name'] and 'adt-script' in monitor['tags']:
            return monitor['id']

    return False


def create_monitor(monitor):
    print('CREATE')
    params = dict(query=monitor['query'],
        name=monitor['name'],
        message=monitor['message'],
        type=monitor['type'],
        options=monitor['options'],
        tags=monitor['tags'])
    print(params)
    # return
    return datadog.api.Monitor.create(**params)


def update_monitor(monitor_id, monitor):
    print('UPDATE')
    params = dict(query=monitor['query'],
        name=monitor['name'],
        message=monitor['message'],
        type=monitor['type'],
        options=monitor['options'],
        tags=monitor['tags'])
    print(params)
    # return
    return datadog.api.Monitor.update(monitor_id, **params)


def delete_extra_monitors(updated_monitors):
    """ Deletes the extra monitors created by 'adt-script' but not updated
    in this run

    :param updated_monitor: list of names of monitors created/updated in this run
    """
    deleted = []
    for monitor in all_monitors:
        if monitor['name'] not in updated_monitors:
            if 'adt-script' in monitor['tags']:
                datadog.api.Monitor.delete(monitor['id'])
                deleted.append(monitor['name'])

    return deleted


class SafeDict(dict):
    """Default class for using in 'format_map' and avoid missing key error"""

    def __missing__(self, key):
        return '{' + key + '}'


# template of a monitor, to be substituted with real values to create monitors
monitor_template = {
    "name": "TEMPLATE NAME PLEASE CHANGE",
    "type": "SPECIFY SERVICE CHECK",
    "query": "SPECIFY QUERY",
    "message": "SPECIFY MESSAGE",
    # "tags": [
    #     "",
    #     "production"
    # ],
    "options": {
        "notify_audit": False,
        "locked": False,
        "timeout_h": 0,
        "silenced": {},
        "include_tags": False,
        # "thresholds": {
        #     "warning": 1,
        #     "critical": 1,
        #     "ok": 1
        # },
        "new_host_delay": 300,
        "notify_no_data": True,
        "renotify_interval": 10,
        "escalation_message": "PLEASE UPDATE",
        "no_data_timeframe": 3,
        "evaluation_delay": "30",
        "require_full_window": False,
    }
}


def monitor_type_service_check():
    monitors = [
        {  # agent up, production
            'environments': [PRODUCTION],
            "query": '"datadog.agent.up".over("environment:{environment}").last(2).count_by_status()',
            "name": "Host is Down ({environment}/{{{{host.name}}}})",
            "message": textwrap.dedent(
                """
                {{#is_alert}}
                #CRITICAL# ({{environment.name}}) Host is down.

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{host.application}}
                - Env: {{host.environment}}

                """ + critical_alerts_notifications + """
                {{/is_alert}}

                {{#is_recovery}}
                Host is up again ({{environment.name}}).

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{host.application}}
                - Env: {{host.environment}}

                """ + recovery_notifications + """
                {{/is_recovery}}
                """),
            'tags': [
                "critical",
                "env-{environment}",
                "adt-script",
                "host-up"
            ],
            "options": {
                "thresholds": {
                    "warning": 1,
                    "critical": 1,
                    "ok": 1
                },
                "renotify_interval": 10,
                "escalation_message": "Host is still down.",
                "no_data_timeframe": 2
            }
        },
        {  # agent up, production
            'environments': [QA],
            "query": '"datadog.agent.up".over("environment:{environment}").last(2).count_by_status()',
            "name": "Host is Down ({environment}/{{{{host.name}}}})",
            "message": textwrap.dedent(
                """
                {{#is_alert}}
                #CRITICAL# ({{environment.name}}) Host is down.

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{host.application}}
                - Env: {{host.environment}}

                """ + critical_alerts_notifications + """
                {{/is_alert}}

                {{#is_recovery}}
                ({{environment.name}}) Host is up again.

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{host.application}}
                - Env: {{host.environment}}

                """ + recovery_notifications + """
                {{/is_recovery}}
                """),
            'tags': [
                "critical",
                "env-{environment}",
                "adt-script",
                "host-up"
            ],
            "options": {
                "thresholds": {
                    "warning": 1,
                    "critical": 1,
                    "ok": 1
                },
                "renotify_interval": 10,
                "escalation_message": "Host is still down.",
                "no_data_timeframe": 2
            }
        },
        {  # agent up, production
            'environments': [DEVELOPMENT],
            "query": '"datadog.agent.up".over("environment:{environment}").last(2).count_by_status()',
            "name": "Host is Down ({environment}/{{{{host.application}}}})",
            "message": textwrap.dedent(
                """
                {{#is_alert}}
                #CRITICAL# ({{environment.name}}) Host is down.

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{host.application}}
                - Env: {{host.environment}}

                """ + critical_alerts_notifications + """
                {{/is_alert}}

                {{#is_recovery}}
                ({{environment.name}}) Host is up again.

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{host.application}}
                - Env: {{host.environment}}

                """ + recovery_notifications + """
                {{/is_recovery}}
                """),
            'tags': [
                "critical",
                "env-{environment}",
                "adt-script",
                "host-up"
            ],
            "options": {
                "thresholds": {
                    "warning": 1,
                    "critical": 1,
                    "ok": 1
                },
                "renotify_interval": 60,
                "escalation_message": "Host is still down.",
                "no_data_timeframe": 2
            }
        },
        {  # agent up, production
            'environments': [''],
            "query": '"datadog.agent.up".over("*").exclude("environment:' + PRODUCTION + '","environment:' +
                     DEVELOPMENT + '","environment:' + QA + '").last(2).count_by_status()',
            "name": "Host is Down ({{{{host.name}}}})",
            "message": textwrap.dedent(
                """
                {{#is_alert}}
                #CRITICAL# Host is down (Not Prod, Dev or QA).

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{host.application}}
                - Env: {{host.environment}}

                """ + critical_alerts_notifications + """
                {{/is_alert}}

                {{#is_recovery}}
                Host is up again.

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{host.application}}
                - Env: {{host.environment}}

                """ + recovery_notifications + """
                {{/is_recovery}}
                """),
            'tags': [
                "critical",
                "adt-script",
                "host-up"
            ],
            "options": {
                "thresholds": {
                    "warning": 1,
                    "critical": 1,
                    "ok": 1
                },
                "renotify_interval": 10,
                "escalation_message": "Host is still down.",
                "no_data_timeframe": 2,
                "new_host_delay": 900,
            }
        },
        {
            "environments": [DEVELOPMENT, PRODUCTION, MANAGEMENT, QA],
            "processes": ["apache", "bamboo", "dsdk_process", "ipsec", "java", "labs-sso", "logstash", "logstash-autostart", "marathon", "mesos-master", "mesos-slave", "mongodb", "openvpnas", "smbd", "ssh", "workerGroup"],
            "name": "Process {process} not running ({{{{host.name}}}}/{environment})",
            "type": "service check",
            "query": '"process.up".over("environment:{environment}","process:{process}").last(1).count_by_status()',
            "message": textwrap.dedent(
                """
                {{#is_alert}}
                #CRITICAL# Process ({{process.name}}/{{environment.name}}) not running ({{host.name}})

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{host.application}}
                - Env: {{host.environment}}

                """ + critical_alerts_notifications + """
                {{/is_alert}}

                {{#is_recovery}}
                Host is up again.

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{host.application}}
                - Env: {{host.environment}}

                """ + recovery_notifications + """
                {{/is_recovery}}
                """),
            'tags': [
                "critical",
                "adt-script",
                "env-{environment}",
                "process-monitoring",
                "process-{process}"
            ],
            "options": {
                "thresholds": {
                    "warning": 1,
                    "critical": 1,
                    "ok": 1
                },
                "renotify_interval": 10,
                "escalation_message": "Process still not running.",
                "no_data_timeframe": 2
            }
        }
    ]
    return monitors


def monitor_type_metric_alerts():
    """simply adds the lists of each type of metric_alert"""
    monitors = monitor_type_metric_alert_cpu() + \
        monitor_type_metric_alert_diskuse() + \
        monitor_type_metric_alert_memory()

    return monitors


def monitor_type_metric_alert_cpu():
    monitors = [
        {  # redshift cpu
            'environments': [''],
            'query': 'avg(last_15m):avg:aws.redshift.cpuutilization{{*,!nodeid:leader}} by {clusteridentifier} > '
                     '{critical_threshold}',
            "name": "RedShift CPU UTILIZATION is High ({{clusteridentifier.name}})",
            "message": textwrap.dedent(
                """
                {{#is_alert}}
                #CRITICAL# RedShift CPU Utilization is High at {{value}}.

                - Cluster name: {{clusteridentifier.name}}

                More info: https://console.aws.amazon.com/redshift/home?region=us-east-1#performance:cluster="""
                """{{clusteridentifier.name}};metrics=

                @slack-alerts-critical-db
                @teams-Datadogalerts
                {{/is_alert}}

                {{#is_recovery}}
                RedShift CPU Utilization is OK at {{value}}.

                - Cluster name: {{clusteridentifier.name}}

                More info: https://console.aws.amazon.com/redshift/home?region=us-east-1#performance:cluster="""
                """{{clusteridentifier.name}};metrics=

                """ + recovery_notifications + """
                {{/is_recovery}}
                """),
            'tags': [
                "critical",
                "RedShift",
                "adt-script"
            ],
            "options": {
                "thresholds": {'critical': 95},
                "escalation_message": "RedShift CPU Utilization is still High",
                "evaluation_delay": "900",
                "renotify_interval": 10,
            }
        },
        {  # prod host cpu
            'environments': ['prod'],
            'query': 'avg(last_15m):avg:system.cpu.user{{environment:{environment}}} by '
                     '{name,application,environment,host} > {critical_threshold}',
            "name": "EC2 CPU UTILIZATION ({environment}/{{{{application.name}}}}) is High",
            "message": textwrap.dedent(
                """
                {{#is_alert}}
                #CRITICAL# ({{environment.name}}) EC2 CPU Utilization is High at {{value}}.

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{application.name}}
                - Env: {{environment.name}}

                """ + critical_alerts_notifications + """
                {{/is_alert}}

                {{#is_warning}}
                #HIGH# ({{environment.name}}) EC2 CPU Utilization is High at {{value}}.

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{application.name}}
                - Env: {{environment.name}}

                """ + high_alerts_notifications + """
                {{/is_warning}}

                {{#is_recovery}}
                EC2 CPU Utilization is OK at {{value}}.

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{application.name}}
                - Env: {{environment.name}}

                """ + recovery_notifications + """
                {{/is_recovery}}
                """),
            'tags': [
                "critical",
                "env-{environment}",
                "high",
                "EC2-CPU",
                "adt-script"
            ],
            "options": {
                "thresholds": {'critical': 95, 'warning': 85},
                "escalation_message": "EC2 CPU Utilization is still High",
                "evaluation_delay": "900",
                "renotify_interval": 30,
            }
        },
        {  # NON prod host cpu
            'environments': ['prod'],
            'query': 'avg(last_15m):avg:system.cpu.user{{!environment:{environment}}} by '
                     '{name,application,environment,host} > {critical_threshold}',
            "name": "EC2 CPU UTILIZATION is High ({{{{environment.name}}}}/{{{{application.name}}}})",
            "message": textwrap.dedent(
                """
                {{#is_alert}}
                #HIGH# EC2 CPU Utilization is High at {{value}}.

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{application.name}}
                - Env: {{environment.name}}

                """ + high_alerts_notifications + """
                {{/is_alert}}

                {{#is_recovery}}
                EC2 CPU Utilization is OK at {{value}}.

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{application.name}}
                - Env: {{environment.name}}

                """ + recovery_notifications + """
                {{/is_recovery}}
                """),
            'tags': [
                "high",
                "EC2-CPU",
                "adt-script",
                "not-env-{environment}"
            ],
            "options": {
                "thresholds": {'critical': 85},
                "escalation_message": "EC2 CPU Utilization is still High",
                "evaluation_delay": "900",
                "renotify_interval": 30,
            }
        },
        {  # rds cpu qa,dev
            'environments': [PRODUCTION],
            'query': 'avg(last_15m):avg:aws.rds.cpuutilization{{environment:{environment}}} by {host,engine,name} > '
                     '{critical_threshold}',
            "name": "RDS CPU UTILIZATION ({environment}/{{{{name.name}}}}) is High",
            "message": textwrap.dedent(
                """
                {{#is_alert}}
                #CRITICAL# RDS CPU UTILIZATION ({{environment.name}}-{{name.name}}) is High at {{value}}.

                - Name: {{name.name}}
                - Host: {{host.name}}
                - Engine: {{engine.name}}

                More info: https://console.aws.amazon.com/rds/home?region=us-east-1#dbinstance:id={{name.name}}

                @slack-alerts-critical-db
                @teams-Datadogalerts
                {{/is_alert}}

                {{#is_warning}}
                #HIGH# RDS CPU UTILIZATION ({{environment.name}}-{{name.name}}) is High at {{value}}.

                - Name: {{name.name}}
                - Host: {{host.name}}
                - Engine: {{engine.name}}

                More info: https://console.aws.amazon.com/rds/home?region=us-east-1#dbinstance:id={{name.name}}

                """ + high_alerts_notifications + """
                    {{/is_warning}}

                    {{#is_recovery}}
                    RDS CPU UTILIZATION ({{environment.name}}-{{name.name}}) is OK at {{value}}.

                    - Name: {{name.name}}
                    - Host: {{host.name}}
                    - Engine: {{engine.name}}

                    More info: https://console.aws.amazon.com/rds/home?region=us-east-1#dbinstance:id={{name.name}}

                    """ + recovery_notifications + """
                    {{/is_recovery}}
                    """),
            'tags': [
                "critical",
                "env-{environment}",
                "high",
                "rds-cpu",
                "adt-script"
            ],
            "options": {
                "thresholds": {'critical': 95, 'warning': 85},
                "escalation_message": "RDS CPU Utilization is still High",
                "evaluation_delay": "900",
                "renotify_interval": 30,
            }
        },
        {  # rds cpu qa,dev
            'environments': [DEVELOPMENT, QA],
            'query': 'avg(last_15m):avg:aws.rds.cpuutilization{{environment:{environment}}} by {host,engine,name} > '
                     '{critical_threshold}',
            "name": "RDS CPU UTILIZATION ({environment}/{{{{name.name}}}}) is High",
            "message": textwrap.dedent(
                """
                {{#is_alert}}
                #CRITICAL# RDS CPU UTILIZATION ({{environment.name}}-{{name.name}}) is High at {{value}}.

                - Name: {{name.name}}
                - Host: {{host.name}}
                - Engine: {{engine.name}}

                More info: https://console.aws.amazon.com/rds/home?region=us-east-1#dbinstance:id={{name.name}}

                """ + high_alerts_notifications + """
                {{/is_alert}}

                {{#is_warning}}
                #HIGH# RDS CPU UTILIZATION ({{environment.name}}-{{name.name}}) is High at {{value}}.

                - Name: {{name.name}}
                - Host: {{host.name}}
                - Engine: {{engine.name}}

                More info: https://console.aws.amazon.com/rds/home?region=us-east-1#dbinstance:id={{name.name}}

                """ + high_alerts_notifications + """
                {{/is_warning}}

                {{#is_recovery}}
                RDS CPU UTILIZATION ({{environment.name}}-{{name.name}}) is OK at {{value}}.

                - Name: {{name.name}}
                - Host: {{host.name}}
                - Engine: {{engine.name}}

                More info: https://console.aws.amazon.com/rds/home?region=us-east-1#dbinstance:id={{name.name}}

                """ + recovery_notifications + """
                {{/is_recovery}}
                """),
            'tags': [
                "critical",
                "env-{environment}",
                "high",
                "rds-cpu",
                "adt-script"
            ],
            "options": {
                "thresholds": {'critical': 95, 'warning': 85},
                "escalation_message": "RDS CPU Utilization is still High",
                "evaluation_delay": "900",
                "renotify_interval": 30,
            }
        },
        {  # rds cpu NOT prod,qa,dev
            'environments': [''],
            'query': 'avg(last_15m):avg:aws.rds.cpuutilization{{'
                     '!environment:' + QA +
                     ',!environment:' + DEVELOPMENT +
                     ',!environment:' + PRODUCTION + '}} ' +
                     'by {host,engine,name} > {critical_threshold}',
            "name": "RDS CPU UTILIZATION ({{{{environment.name}}}}/{{{{name.name}}}}) is High",
            "message": textwrap.dedent(
                """
                {{#is_alert}}
                #CRITICAL# RDS CPU UTILIZATION ({{name.name}}) is High at {{value}}.

                - Name: {{name.name}}
                - Host: {{host.name}}
                - Engine: {{engine.name}}

                More info: https://console.aws.amazon.com/rds/home?region=us-east-1#dbinstance:id={{name.name}}

                """ + recovery_notifications + """
                {{/is_alert}}

                {{#is_warning}}
                #HIGH# RDS CPU UTILIZATION ({{name.name}}) is High at {{value}}.

                - Name: {{name.name}}
                - Host: {{host.name}}
                - Engine: {{engine.name}}

                More info: https://console.aws.amazon.com/rds/home?region=us-east-1#dbinstance:id={{name.name}}

                """ + high_alerts_notifications + """
                {{/is_warning}}

                {{#is_recovery}}
                RDS CPU UTILIZATION ({{name.name}}) is OK at {{value}}.

                - Name: {{name.name}}
                - Host: {{host.name}}
                - Engine: {{engine.name}}

                More info: https://console.aws.amazon.com/rds/home?region=us-east-1#dbinstance:id={{name.name}}

                """ + recovery_notifications + """
                {{/is_recovery}}
                """),
            'tags': [
                "critical",
                "high",
                "rds-cpu",
                "adt-script"
            ],
            "options": {
                "thresholds": {'critical': 95, 'warning': 85},
                "escalation_message": "RDS CPU Utilization is still High",
                "evaluation_delay": "900",
                "renotify_interval": 30,
            }
        },
    ]

    return monitors


def monitor_type_metric_alert_diskuse():
    monitors = [
        {  # disk use
            'environments': [PRODUCTION, DEVELOPMENT, QA, MANAGEMENT],
            'query': 'avg(last_10m):avg:system.disk.in_use{{environment:{environment},!device:/dev/nvme0n1p1, !device:/dev/nvme1n1, !device:/dev/loop0, !device:/dev/loop1, !device:/dev/loop2, !device:/dev/loop3, !device:/dev/loop4}} by {name,application,environment,host,device} > {critical_threshold}',
            "name": "Disk Space Usage ({environment}/{{{{application.name}}}}) is High",
            "message": textwrap.dedent(
                """
                {{#is_alert}}
                #HIGH# ({{environment.name}}) Disk Space Usage is High at {{value}}.

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{application.name}}
                - Env: {{environment.name}}
                - Device: {{device.name}}

                """ + high_alerts_notifications + """
                {{/is_alert}}

                {{#is_recovery}}
                ({{environment.name}}) Disk Space Usage is OK at {{value}}.

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{application.name}}
                - Env: {{environment.name}}

                """ + recovery_notifications + """
                {{/is_recovery}}
                """),
            'tags': [
                "high",
                "env-{environment}",
                "disk-use",
                "adt-script"
            ],
            "options": {
                "thresholds": {'critical': 0.85},
                "escalation_message": "Disk Space Usage is still High.",
                "renotify_interval": 4*60,  # 4 hours
                "no_data_timeframe": 20
            }
        },
        {  # rds used storage space
            "environments": [PRODUCTION, DEVELOPMENT, QA, MANAGEMENT],
            "name": "RDS Storage ({environment}/{{{{dbname.name}}}})",
            "type": "metric alert",
            "query": "avg(last_1h):( avg:aws.rds.total_storage_space{*} by {dbname,environment} - avg:aws.rds.free_storage_space{*} by {dbname,environment} ) / avg:aws.rds.total_storage_space{*} by {dbname,environment} * 100 > {critical_threshold}",
            "message": textwrap.dedent(
                """
                {{#is_alert}}
                #CRITICAL# ({{environment.name}} / {{dbinstanceidentifier.name}} ) RDS Disk Space Usage is Critical at {{value}}.

                - DBInstanceIdentifier Name: {{dbinstanceidentifier.name}}
                - DB Name: {{dbname.name}}
                - Env: {{environment.name}}

                """ + critical_alerts_notifications + """
                {{/is_alert}}

                {{#is_warning}}
                #HIGH#  ({{environment.name}} / {{dbinstanceidentifier.name}} ) RDS Disk Space Usage is High at {{value}}.

                - DBInstanceIdentifier Name: {{dbinstanceidentifier.name}}
                - DB Name: {{dbname.name}}
                - Env: {{environment.name}}

                """ + high_alerts_notifications + """
                {{/is_warning}}

                {{#is_recovery}}
                RDS Disk Space Usage is OK in {{dbinstanceidentifier.name}} at {{value}}.

                - DBInstanceIdentifier Name: {{dbinstanceidentifier.name}}
                - DB Name: {{dbname.name}}
                - Env: {{environment.name}}

                """ + recovery_notifications + """
                {{/is_recovery}}
                """),
            'tags': [
                "high",
                "critical",
                "env-{environment}",
                "rds-disk",
                "disk-use",
                "adt-script"
            ],
            "options": {
                "escalation_message": "RDS Disk Space Usage is still High.",
                "thresholds": {
                    "critical": 90,
                    "warning": 85
                },
                "no_data_timeframe": 120
            }
        }
    ]

    return monitors


def monitor_type_metric_alert_memory():
    monitors = [
        {
            'environments': [PRODUCTION, DEVELOPMENT, QA, MANAGEMENT],
            'query': 'avg(last_10m):avg:system.mem.pct_usable{{environment:{environment}}} by '
                     '{name,application,environment,host} < {critical_threshold}',
            "name": "Memory Pct Usable ({environment}/{{{{application.name}}}}) is Low",
            "message": textwrap.dedent(
                """
                {{#is_alert}}
                #HIGH# ({{environment.name}}) Memory Pct Usable is Low at {{value}}.

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{application.name}}
                - Env: {{environment.name}}

                """ + high_alerts_notifications + """
                {{/is_alert}}

                {{#is_recovery}}
                ({{environment.name}}) Memory Pct Usable is OK at {{value}}.

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{application.name}}
                - Env: {{environment.name}}
                """ + recovery_notifications + """
                {{/is_recovery}}
                """),
            'tags': [
                "high",
                "env-{environment}",
                "memory",
                "adt-script"
            ],
            "options": {
                "thresholds": {'critical': 0.10},
                "escalation_message": "Memory Pct Usable is still Low.",
                "renotify_interval": 30,
            }
        },
        {
            'environments': [''],
            'query': 'avg(last_10m):avg:system.mem.pct_usable{{'
                     '!environment:' + PRODUCTION +
                     ',!environment:' + DEVELOPMENT +
                     ',!environment:' + QA +
                     ',!environment:' + MANAGEMENT + '}} '
                     'by {name,application,environment,host} < {critical_threshold}',
            "name": "Memory Pct Usable ({{{{application.name}}}}) is Low",
            "message": textwrap.dedent(
                """
                {{#is_alert}}
                #HIGH# ({{environment.name}}) Memory Pct Usable is Low at {{value}}.

                - Host: {{host.name}}, IP: {{host.ip}}
                - App: {{application.name}}
                - Env: {{environment.name}}

                """ + high_alerts_notifications + """
                    {{/is_alert}}

                    {{#is_recovery}}
                    ({{environment.name}}) Memory Pct Usable is OK at {{value}}.

                    - Host: {{host.name}}, IP: {{host.ip}}
                    - App: {{application.name}}
                    - Env: {{environment.name}}
                    """ + recovery_notifications + """
                    {{/is_recovery}}
                    """),
            'tags': [
                "high",
                "env-{environment}",
                "Memory",
                "adt-script"
            ],
            "options": {
                "thresholds": {'critical': 0.10},
                "escalation_message": "Memory Pct Usable is still Low.",
                "renotify_interval": 30,
            }
        }
    ]

    return monitors

monitor_types = {
    ############################# SERVICE CHECK
    'service check': monitor_type_service_check(),

    ############################# METRIC ALERTS
    'metric alert': monitor_type_metric_alerts(),

    # 'memory_usage': [
    #     {
    #         'environment': [PRODUCTION],
    #         "thresholds": {'critical': 99, 'warning': 98,  'critical_recovery': 97, 'warning_recovery': 96}
    #     },
    #     {
    #         'environment': [DEVELOPMENT, QA, MANAGEMENT],
    #         "thresholds": {'critical': 99, 'warning': 98,  'critical_recovery': 97, 'warning_recovery': 96}
    #     }
    # ],
    # 'cpu_utilization': [
    #     {
    #         'environment': [PRODUCTION],
    #         "thresholds": {'critical': 99, 'warning': 98,  'critical_recovery': 97, 'warning_recovery': 96}
    #     },
    #     {
    #         'environment': [DEVELOPMENT, QA, MANAGEMENT],
    #         "thresholds": {'critical': 99, 'warning': 98,  'critical_recovery': 97, 'warning_recovery': 96}
    #     }
    # ]
}

updated_monitors = []

monitor_changes = {'created': [], 'updated': [], 'deleted': []}
for (monitor_type, monitors) in monitor_types.items():
    for monitor in monitors:
        # pprint(monitor_type)
        # pprint(monitors)
        # pprint(monitor)
        for environment in monitor["environments"]:
            if "processes" not in monitor:
                monitor["processes"] = ["none"]
            for process in monitor["processes"]:
                print('.', end="", flush=True)
                # print(monitor['name'])
                # print(monitor['query'])

                # making a deepcopy of dictionary, and later modify and merge copies
                alert_monitor = copy.deepcopy(monitor)
                monitor_template_copy = copy.deepcopy(monitor_template)

                alert_monitor['tags'].append(monitor_type)
                alert_monitor['type'] = monitor_type

                # substituting variables that might be present in certain keys in alert_monitor
                for i in range(len(alert_monitor["tags"])):
                    alert_monitor["tags"][i] = alert_monitor["tags"][i].format_map(SafeDict(
                        environment=environment,
                        process=process
                    ))

                for k in ['query', 'name', "process"]:
                    if k in alert_monitor:
                        alert_monitor[k] = alert_monitor[k].format_map(SafeDict(
                            environment=environment,
                            critical_threshold=monitor['options']['thresholds']['critical'],
                            process=process,
                        ))

                dict_merge(monitor_template_copy, alert_monitor)

                # pprint(alert_monitor)
                # sys.exit()

                monitor_name = monitor_template_copy['name']
                if monitor_name in updated_monitors:
                    print("Error: A monitor with name `{}` has already been created/updated".format(monitor_name))
                    sys.exit()

                monitor_id = get_monitor_id(monitor_name)

                result = None
                if monitor_id is False:
                    monitor_changes['created'].append(monitor_name)
                    # create new monitor
                    result = create_monitor(monitor_template_copy)
                else:
                    monitor_changes['updated'].append(monitor_name)
                    # update monitor
                    result = update_monitor(monitor_id, monitor_template_copy)

                updated_monitors.append(monitor_name)

                if result and 'modified' not in result:
                    print("Error:")
                    pprint(monitor_template_copy)
                    pprint(result)
                    sys.exit()

# deletes the extra monitors created by 'adt-script' that were not updated in this run
monitor_changes['deleted'] = delete_extra_monitors(updated_monitors)

print()
pprint(monitor_changes)
