import json
import annalect_helper as ah


req = ah.submit_job(
    appName="kates_container",
    jobCommand="python3 my_script.py",
    arguments={"name": "jane doe"},
    jobName="intuit-generating-images-101010"
)


print(req.text)