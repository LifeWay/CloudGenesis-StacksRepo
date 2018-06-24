# GitFormation: GitOps Repo of Stacks and Templates

When using GitFormation, obviously you have to have a Git repo to host your Stack and Template files. This repo consists
of the minimum files necessary to ensure that when GitFormation runs the `buildspec-pr.yaml` and `buildspec-sync.yaml`
files that your templates will be validated (PR) and on merge, your templates and stacks will be sync'd with your 
S3 bucket.

The purpose of this repo is to sync a given GitHub Repo to an S3 bucket, and only touch files in S3 that have 
actually changed (e.g. don't re-upload everything every time). Additionally, this project is responsible for doing some 
basic validations / linting of CF templates prior to merge and again during the sync to s3 process.

* Validates all templates via CloudFormations template validation API.
* Basic security linting via CF_NAG
* Other linters or validators as they become available.

## How to use day-to-day:
There is two main directories: `stacks` and `templates`.

### Templates:
These are your literal cloud formation templates. Nothing special. Please be aware that downstream automation does not 
do any package and deploy steps. So this automation is not well suited for Serverless Transforms where the CodeUri is 
referring to a local path (vs an S3 path which would not need SAM packaging). HOWEVER, GitFormation *DOES* create change
sets with each deploy - so you are free to use SAM and other transforms in your stacks so long as the template does not
to be run through the aws cli packager first (e.g. SAM templates with relative CodeUri's).

### Stacks:
Stacks are the definition of the various parameters, tags, and the template needed to actually launch one of your templates 
making it a stack. The folder structure of stacks is important:

Sample structure:
```text
stacks/
  account-alias.123456789/
    us-east-1
      whatever/structure/i/want
        my-stack.yaml
  234567891/
    us-west-2
      some/other/structure
        another-stack.yaml
``` 

The key above is that the first sub dir under `stacks/` represents the AWS account you want your stack deployed into. 
The `account-alias` is OPTIONAL and does not need to match your actual account alias if you use one. It is purely for 
your ease of use when looking at the directories. The only thing that actually matters is the accountId porition which 
is parsed out of the alias following the first `.` in the alias name.

The second sub directory under your account Id directory is the REGION directory. This directory name must be named 
using the standard AWS region id code. See [AWS documentation for the list of valid values](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/using-regions-availability-zones.html#concepts-available-regions)


### Secret Parameter Values
CloudFormation does not yet support SSM values as a parameter where that value is a secret string yet. This can cause 
quite a headache when practicing GitOps for Cloudformation as you MUST be able to pass the secret paramater in source 
somehow, otherwise you would have to revert back to launching the stack by hand.

GitFormation handles this issue by using SSM directly. What GitFormation does is you grant GitFormation itself access to 
read secrets stored at a given SSM path prefix (e.g. `/gitformation/secrets/`). GitFormation when it sees in the stack 
yaml a paramter by the type of `SSM` uses the value field as the key to look up in SSM. GitFormation then reads your 
secret and passes the value of that secret to your stack parameter. 

*WARNING* Because this is not a native CloudFormation feature, that means that the value of your secret gets passed to 
your template just like any other paramter. Your TEMPLATE must be smart enough to know that it needs to have a 
`NoEcho: true` property set on the parameter so that CloudFormation will not show the secret value when describing the 
stack

Here is an example stack file:
```yaml
# stacks/account-alias.123456789/us-east-2/some/folder/my-stack.yaml
---
Template: iam-resources/codebuild-service-role.yaml
Tags:
  - Key: Department
    Value: my-department-name
  - Key: Owner
    Value: my-team-name
  - Key: Environment
    Value: dev
Parameters:
  - Name: BuildNamePrefix
    Value: some-random-param-value
  - Name: AnotherParam
    Value: another-param-value
  - Name: SecretParam
    Type: SSM
    Value: /ssm-path/to/secret/string/
```

### Updating Stacks
Commonly, you will update a template to add new resources, modify a resource etc. Only updating a teplate will have no 
effect on your existing stacks using that template. To have a stack update, you MUST update the stack file in some way. 
This does not need to be a literal change to the stack values, just the file itself must change. So a simple YAML 
comment on a stack is all that is needed to trigger a stack to update. GitFormation ALWAYS passes the template on every 
update (never re-uses existing template). So if a template was updated since the last time the stack was updated, then 
the stack will receive an udpate just from your YAML comment.
