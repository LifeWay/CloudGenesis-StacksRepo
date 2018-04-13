FROM amazonlinux:latest

MAINTAINER Ryan Means <ryan.means@lifeway.com>

RUN yum -y update && \
 yum -y install ruby22 && \
 yum -y install python36 python36-virtualenv python36-pip && \
 yum -y install git

RUN python3.6 -m pip install awscli --upgrade

RUN python3.6 -m pip install gitpython

# Do we want to run unit tests?
# RUN python3.6 -m pip install -U pytest

RUN gem install cfn-nag

RUN yum clean all