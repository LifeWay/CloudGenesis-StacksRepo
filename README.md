# Automated CloudFormation S3 Sync

The purpose of this project is to sync a given GitHub Repo to an S3 bucket, and only touch files in S3 that have actually changed (e.g. don't re-upload everything every time)

Additionally, this project is responsible for doing some basic validations / linting of CF templates prior to merge and again during the sync to s3 process.

* Validates all templates via CloudFormations template validation API.
* Basic security linting via CF_NAG
* Other linters or validators as they become available.

## How to use day-to-day:
There is two main directories: `stacks` and `templates`.

### Templates:
These are your literal cloud formation templates. Nothing special. Please be aware that downstream automation does not do any package and deploy steps. So this automation is not well suited for Serverless Transforms where the CodeUri is referring to a local path (vs an S3 path which would not need SAM packaging)

It would be best practice to structure your templates directory with folders, etc as to the way it maps to your org or products.

### Stacks:
Stacks are the definition of the various parameters, tags, the template needed to actually launch one of your templates making it a stack. The folder structure of stacks is important:

Sample structure:
```text
stacks/
  account-alias.123456789/
    whatever/structure/i/want
  234567891/
    some/other/structure
``` 

The key above is that the first sub dir under `stacks/` represents the AWS account you want your stack deployed into. The `account-alias` is OPTIONAL and does not need to match your actual account alias if you use one. It is purely for your ease of use when looking at the directories. The only thing that actually matters is the accountId porition which is parsed out of the alias following the first `.` in the alias name.

Here is an example stack file:
```yaml
# stacks/account-alias.123456789/some/folder/my-stack.yaml
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
```
WARNING: this process does not work well for Secret params (e.g. `NoEcho`). Those kind of stacks may still need to be launched manually at this time. In the future, when CloudFormation supports SecureString params from SSM, that process can be used instead. See this blog post: https://aws.amazon.com/blogs/mt/integrating-aws-cloudformation-with-aws-systems-manager-parameter-store/

## Deploying the CodeBuild / CodePipeline Jobs:
* Use the `Dockerfile` to build an AWS ECR image for the CodeBuild job - pick your own repo.
* Deploy the `templates/automation-setup-template.yaml` to manage a given repo.
  * ProTip: for child repos that have more granular permissions (e.g. no IAM), have a master repo that does IAM deploys also manage the setup for others. 
