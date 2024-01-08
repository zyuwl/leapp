#! /bin/bash

# Author: yunqi.zwt@alibaba-inc.com

rm -rf pkgs
mkdir pkgs
chmod +x download_offline_rpms.sh
sudo docker run --net=host --name download_offline --rm -v `pwd`/download_offline_rpms.sh:/root/download_offline_rpms.sh -v `pwd`/pkgs/:/mnt/ -v `pwd`/repos_`uname -m`:/etc/yum.repos.d centos:7 bash -c '/root/download_offline_rpms.sh /mnt/'

echo "downloading rpms"
sudo docker wait download_offline

#tmp solution
wget https://gitee.com/src-anolis-sig/migrear/raw/master/migrear -O pkgs/migrear

tar -czvf anolis_migration_pkgs_`uname -m`.tar.gz pkgs
