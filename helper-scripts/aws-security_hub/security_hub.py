import os
import csv
import json
import yaml
from datetime import datetime
from pydantic import BaseModel
from pydantic.json import pydantic_encoder
from typing import List

class Finding(BaseModel):
    environment: str = ''
    account_id: str = ''
    created_at: str = ''
    updated_at: str = ''
    compliance_status: str = ''
    title: str = ''
    description: str = ''
    recommendation_text: str = ''
    recommendation_url: str = ''
    workflow_state: str = ''
    workflow_status: str = ''
    record_state: str = ''
    severity_label: str = ''

def fetch_findings(environment: str, filterstr: str, sortcriteria: str) -> List[Finding]:
    '''
        Fetches the findings from a given aws account following a certain filter and sorting criteria
    '''

    os.environ['AWS_PROFILE'] = environment

    findings_raw = os.popen(f'aws securityhub get-findings --filters {filterstr} --sort-criteria {sortcriteria} --region us-east-1 --page-size 100 --max-items 1000')
    findings_json = json.loads(findings_raw.read())['Findings']

    findings: List[Finding] = []
    for f in findings_json:
        finding = Finding()
        finding.environment = environment
        finding.account_id = f['AwsAccountId']
        finding.created_at = f['CreatedAt']
        finding.updated_at = f['UpdatedAt']
        finding.compliance_status = f["Compliance"]["Status"] if ("Compliance" in f.keys()) else ''
        finding.title = f["Title"]
        finding.description = f["Description"]
        finding.recommendation_text = f["Remediation"]["Recommendation"]["Text"] if ("Remediation" in f.keys()) else ''
        finding.recommendation_url = f["Remediation"]["Recommendation"]["Url"] if ("Remediation" in f.keys() and "Url" in f["Remediation"]["Recommendation"].keys()) else ''
        finding.workflow_state = f["WorkflowState"]
        finding.workflow_status = f["Workflow"]["Status"]
        finding.record_state = f["RecordState"]
        finding.severity_label = f["FindingProviderFields"]["Severity"]["Label"]

        findings.append(finding)

    return findings

def create_valid_csv(findings: List[Finding]):
    with open(f'security_findings_{datetime.now().strftime("%Y%m%d")}.csv', 'w', newline='') as csvfile:
        fieldnames = Finding.__annotations__.keys()
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for index, finding in enumerate(findings):
            finding_dict = json.loads(json.dumps(finding, default=pydantic_encoder))
            writer.writerow(finding_dict)

if __name__ == '__main__':

    settings = None
    with open('settings.yaml', 'r') as stream:
        settings = yaml.safe_load(stream)

    # fetch environments and build filters and sorting criteria
    environments = settings['accounts']
    filterstr = '\'{' + ','.join(f'"{x["filter_name"]}": [{{"Value": "{x["value"]}", "Comparison": "{x["comparison"]}"}}]' for x in settings['filters'])
    filterstr += ',"SeverityLabel": [{"Value": "HIGH", "Comparison": "EQUALS"}, {"Value": "LOW", "Comparison": "EQUALS"}, {"Value": "CRITICAL", "Comparison": "EQUALS"}, {"Value": "MEDIUM", "Comparison": "EQUALS"}]'
    filterstr += "}'"
   
    sortcriteria = f'\'{{"Field": "{settings["sort_criteria"]["field"]}", "SortOrder": "{settings["sort_criteria"]["sort_order"]}"}}\''

    # fetch all findings and create a html report
    findings = [finding for env in environments for finding in fetch_findings(environment=env, filterstr=filterstr, sortcriteria=sortcriteria)]
    create_valid_csv(findings=findings)

    print(f'Finished, Found: {len(findings)} finding(s)')
    