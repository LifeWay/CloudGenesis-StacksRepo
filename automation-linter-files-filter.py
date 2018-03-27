#!/usr/bin/env python

"""automation-linter-files-filter.py:
This script compares what is in the S3 bucket to what came over from the git repo. We take capture the files that are
being changed so that they can be linted and tested prior to launch without re-testing / re-linting the entire repo.

We do this by intentionally using the same tool with the same options that will upload the files (so we have the same
set), but passing a dryrun flag so that the operation doesn't actually occur.
"""

import os
import shutil
from subprocess import run, PIPE

dir_path = os.path.dirname(os.path.realpath(__file__))
os.makedirs("templates-sync/templates", exist_ok=True)
os.makedirs("stacks-sync/stacks", exist_ok=True)

def createChangeSets(dir, basePath):
    s3sync = run(["aws", "s3", "sync", dir, "s3://test-cloudformation-event-bucket", "--dryrun", "--profile=sandboxadmin"], stdout=PIPE, check=True)
    items = s3sync.stdout.decode('UTF-8').split("\n")
    for line in items:
        if line.startswith("(dryrun) upload: "):
            endChar = line.index(" to ")
            path = line[17:endChar]
            filePath = basePath + "/" + path
            os.makedirs(os.path.dirname(filePath), exist_ok=True)
            shutil.copy2(path, filePath)
            # Run CloudFormation template validator against templates.
            if dir == "templates":
                run(["aws", "cloudformation", "validate-template", "--output=text", "--template-body", "file://" + filePath], check=True)

createChangeSets("templates", "templates-sync")
createChangeSets("stacks", "stacks-sync")
