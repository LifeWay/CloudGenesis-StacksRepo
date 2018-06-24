# AWS CodeBuild Docker File.
#
# This docker file is used to build the CodeBuild docker image that the `buildspec-pr.yml` and `buildspec-sync.yml`
# files use during the build process. Every tool that you use in those files to sync your files and run linters and
# validators should ideally be installed in this docker image.
#
# You will need to push this docker image to the ECR repository after you build it.
# 
# NOTE: GitFormation's project repo contains a `template-ecr-buildimage.yaml` setup file that creates the ECR repo for
# you. You must either use that template to create the ECR repo OR you must create your own CloudFormation template that
# creates an ECR. The GitFormation SAM stack requires you to pass the ECR Repo name into the stack.
FROM amazonlinux:latest

MAINTAINER Ryan Means <ryan.means@lifeway.com>

RUN yum -y update && \
 yum -y install ruby22 && \
 yum -y install python36 python36-virtualenv python36-pip

RUN python3.6 -m pip install boto boto3 pytest

RUN gem install cfn-nag

RUN yum clean all
