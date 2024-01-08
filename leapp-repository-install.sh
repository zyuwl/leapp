#! /bin/bash

if [[ "$1" == "-v" ]];then
    echo "Use -v"
elif [ ! -n "$1" ];then
    echo "Default mode"
else
    echo "Please use the correct method"
    exit 0
fi

while getopts "v:" opt; do
    case $opt in
      v)
        if [[ "$OPTARG" == "8.2" ]];then
            echo "put $OPTARG with -v"
            sed -i "s/anolis\/\(\w*\.*\w*\)\//anolis\/$OPTARG\//g" ./leapp_upgrade_repositories.repo
        elif [[ "$OPTARG" == "8.4" ]];then
            echo "put $OPTARG with -v"
            sed -i "s/anolis\/\(\w*\.*\w*\)\//anolis\/$OPTARG\//g" ./leapp_upgrade_repositories.repo
        else
            echo "-v $OPTARG is not available"
            exit 0
        fi
        ;;
      \?)
        echo "Please use -v only"
        exit 0
        ;;
    esac
done

if [ -d /usr/share/leapp-repository ]; then
	echo "leapp-reposiroty is already installed."
	exit 0
fi

# check deps
deps_list=(dnf pciutils libselinux-python policycoreutils-python patch)
for dep in ${deps_list[@]}
do
	rpm -q $dep > /dev/null
	if [ $? -ne 0 ]; then
		echo "$dep is not installed, but is required by leapp-repository"
		echo "It will install $dep first"
		yum -y install $dep
	fi
done

# check dnf version
dnf_version=$(rpm -q dnf --qf "%{VERSION}")
ret=$(awk -v num1=$dnf_version -v num2=4 'BEGIN{print(num1>=num2)?"0":"1"}')
if [ $ret == "1" ]; then
	echo "dnf version is too low to run leapp, please update dnf"
	exit 1
fi

# check glib2 version
glib2_version=$(rpm -q glib2 --qf "%{VERSION}")
ret=$(awk -v num1=$glib2_version -v num2=2.56.1 'BEGIN{print(num1>=num2)?"0":"1"}')
if [ $ret == "1" ]; then
	echo "glib2 version is too low to run leapp, please update glib2"
	exit 1
fi

version=0.13.3
rm -rf leapp-repository-$version
tar xf leapp-repository-${version}.tar.gz
cd leapp-repository-$version
for p in $(ls ../00*.patch)
do
	patch -p1 < $p
done
tar xf ../deps-pkgs-*.tar.gz
mv leapp-deps-*.rpm leapp-repository-deps-*.rpm repos/system_upgrade/el7toel8/files/bundled-rpms/

mkdir -p /usr/share/leapp-repository/custom-repositories
mkdir -p /usr/share/leapp-repository/repositories

cp -r repos/common repos/system_upgrade /usr/share/leapp-repository/repositories
mkdir -p /etc/leapp
mkdir -p /etc/leapp/repos.d
mkdir -p /etc/leapp/transaction
mkdir -p /etc/leapp/files
cp ../leapp_upgrade_repositories.repo /etc/leapp/files
cp ../pes-events.json /etc/leapp/files
cp ../repomap.csv /etc/leapp/files
cp etc/leapp/transaction/to_install etc/leapp/transaction/to_keep etc/leapp/transaction/to_remove /etc/leapp/transaction

rm -rf /usr/share/leapp-repository/repositories/containerization
rm -rf /usr/share/leapp-repository/repositories/test
rm -rf /usr/share/leapp-repository/repositories/common/actors/testactor

find /usr/share/leapp-repository/repositories/common -name "test.py" -delete
rm -rf `find /usr/share/leapp-repository/repositories/ -name "tests" -type d`
find /usr/share/leapp-repository/repositories/ -name "Makefile" -delete

for DIRECTORY in $(find  /usr/share/leapp-repository/repositories/  -mindepth 1 -maxdepth 1 -type d)
do
	REPOSITORY=$(basename $DIRECTORY)
	echo "Enabling repository $REPOSITORY"
	rm -rf /etc/leapp/repos.d/$REPOSITORY
	ln -s /usr/share/leapp-repository/repositories/$REPOSITORY /etc/leapp/repos.d/$REPOSITORY
done

cd ../
rm -rf leapp-repository-${version}
echo "install leapp-repository successfully."


