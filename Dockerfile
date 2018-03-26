FROM amazonlinux:latest

MAINTAINER Ryan Means <ryan.means@lifeway.com>

RUN yum -y update && \
 yum -y install ruby24 && \
 yum -y install python36 python36-virtualenv python36-pip

RUN python3.6 -m pip install awscli --upgrade --user

RUN python3.6 -m pip  install gitpython

RUN yum clean all