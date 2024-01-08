#! /bin/bash

downloaddir=$1
yum install -y python-pip
yum remove -y python-requests python-urllib3; pip uninstall requests urllib3 -y 2>/dev/null || echo "not installed"
yum update -y -xcentos-release --disablerepo=migration
yum install -y leapp --enablerepo=migration
yum remove -y leapp leapp-deps leapp-repository leapp-repository-deps python2-leapp snactor python2-psutil python3-psutil python36-psutil
yum install --downloadonly --downloaddir=${downloaddir} leapp
