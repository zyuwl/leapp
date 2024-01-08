#! /bin/bash

deps_list=(python-six python-setuptools python-requests findutils patch)
for dep in ${deps_list[@]}
do
	rpm -q $dep > /dev/null
	if [ $? -ne 0 ]; then
		echo "$dep is not installed, but is required by leapp"
		echo "It will install $dep first"
		yum -y install $dep
	fi
done

# check python-urllib3
rpm -q python-urllib3 > /dev/null 2>&1
if [ $? -ne 0 ]; then
	echo "python-urllib3 is not installed successfully"
	pip uninstall -y requests urllib3
	yum -y reinstall python-requests
fi

version=0.12.0
tar xf leapp-${version}.tar.gz
cd leapp-${version}
for p in $(ls ../leapp*.patch)
do
	patch -p1 < $p
done
/usr/bin/python2 setup.py build

cp man/snactor.1 /usr/share/man/man1
mkdir -p /usr/share/leapp
mkdir -p /usr/share/leapp/report_schema
cp report-schema-v110.json /usr/share/leapp/report_schema/report-schema.json
mkdir -p /var/lib/leapp
mkdir -p /etc/leapp
mkdir -p /etc/leapp/repos.d
mkdir -p /etc/leapp/answers
mkdir -p /var/log/leapp
cp etc/leapp/leapp.conf /etc/leapp
cp etc/leapp/logger.conf /etc/leapp
cp man/leapp.1 /usr/share/man/man1

/usr/bin/python2 setup.py install -O1 --skip-build --root /
cd ../
rm -rf leapp-$version
echo "Install leapp successfully."

