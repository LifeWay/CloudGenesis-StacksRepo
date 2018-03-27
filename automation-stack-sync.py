from subprocess import run
import yaml

with open("automation-config.yaml", 'r') as ymlconfig:
    config = yaml.load(ymlconfig)

s3bucket = config['Bucket']

def deleteStacks(path):
    # DELETE OLD STACKS FIRST (raise exception on error)
    with open(path) as f:
        content = f.readlines()

    for item in content:
        path = item.strip()
        run(["aws", "s3", "rm", "s3://" + s3bucket + "/" + path], check=True)

deleteStacks("stacks-to-delete.txt")
deleteStacks("templates-to-delete.txt")

#  SYNC TEMPLATES (raise exception on error)
run(["aws", "s3", "sync", "templates-sync/templates", "s3://" + s3bucket, "--size-only", "--delete"], check=True)

# SYNC STACKS (raise exception on error)
run(["aws", "s3", "sync", "stacks-sync/stacks", "s3://" + s3bucket, "--size-only", "--delete"], check=True)
