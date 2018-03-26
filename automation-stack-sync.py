from subprocess import run
import yaml

with open("automation-config.yaml", 'r') as ymlconfig:
    config = yaml.load(ymlconfig)

s3bucket = config['Bucket']

# DELETE OLD STACKS FIRST (raise exception on error)
with open("to-delete.txt") as f:
    content = f.readlines()

for item in content:
    path = item.strip()
    removed = run(["aws", "s3", "rm", "s3://" + s3bucket + "/" + path, "--dryrun"], check=True)

#  SYNC TEMPLATES (raise exception on error)
templateSync = run(["aws", "s3", "sync", "templates-changed/templates", "s3://" + s3bucket, "--size-only", "--delete", "--dryrun"], check=True)

# SYNC STACKS (raise exception on error)
stackSync = run(["aws", "s3", "sync", "stacks-changed/stacks", "s3://" + s3bucket, "--size-only", "--delete"], check=True)
