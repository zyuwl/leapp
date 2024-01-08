#!/usr/bin/env bash

[ "$EUID" -eq 0 ] || {
    echo "Please run this script as a root user"
    exit 1
}

export MIRROR_SITE="http://mirrors.cloud.aliyuncs.com"
mirror_site="${MIRROR_SITE:-https://mirrors.openanolis.cn}"

report_error_in_jsonfile() {
    unixtime=$(date +%s)
    errMsg_inline=$(echo -e "$3" | tr -d '\n\r\t"\\')
    printf '{"Timestamp":%s,"ProgressInfo":"%s","Progress":0,"ErrorCode":%s,"ErrorMsg":"%s"}' "$unixtime" "$1" "$2" "${errMsg_inline: -1900}" > "$jsonfile"
}

check_if_centos_or_rhel() {
    [ -f /etc/centos-release ] && return 0
    [ -f /etc/redhat-release ] && return 0
    echo "CANNOT find /etc/centos-release or /etc/redhat-release, WONT install migration tool"
    out=$(cat /etc/system-release)
    report_error_in_jsonfile "unsupported version" 103 "$out"
    exit 1
}

disable_migration_repo() {
    sed -i "s/enabled=1/enabled=0/" /etc/yum.repos.d/anolis-migration.repo
}

disable_yum_exclude() {
    sed -i '/exclude=/ s/^/#/' /etc/yum.conf
}

# config epel
epel_repo_config() {
    rpm -q epel-release || rpm -q epel-aliyuncs-release && [ -f /etc/yum.repos.d/epel.repo ] && return 0
    # maybe using filename epel-7.repo since this guide https://developer.aliyun.com/mirror/epel
    rpm -q epel-release || rpm -q epel-aliyuncs-release && [ -f /etc/yum.repos.d/epel-7.repo ] && return 0
    rpm -q epel-release || rpm -q epel-aliyuncs-release && [ -f /etc/yum.repos.d/CentOS-Linux-epel.repo ] && return 0

    if rpm -q epel-release || rpm -q epel-aliyuncs-release 
    then
        :
    else
        out=$(yum install -y epel-release 2>&1)
    fi
    exit_code=$?
    if [ "$exit_code" -ne 0 ]
    then
        echo "failed to install epel-release"
        out+="\n$(ls /etc/yum.repos.d)"
        out+="\n$(cat /etc/yum.conf|grep '='|grep -v '#')"
        report_error_in_jsonfile "install epel-release" 103 "$out"
        exit 1
    fi

    # set better mirror site
    sed -i 's|^enabled=1|enabled=0|' /etc/yum.repos.d/*epel*
    major_release=$(cat /etc/os-release |grep -w VERSION_ID | sed 's/.*"\(.*\)".*/\1/g' | awk -F'.' '{print $1}')
    if [ "$major_release" -eq 7 ] || [ "$major_release" -eq 2 ]
    then
        cat << EOF > /etc/yum.repos.d/epel.repo
[epel]
name=Extra Packages for Enterprise Linux 7 - \$basearch
baseurl=https://mirrors.aliyun.com/epel/7/\$basearch
        http://mirrors.cloud.aliyuncs.com/epel/7/\$basearch
failovermethod=priority
enabled=1
gpgcheck=0
EOF
    elif [ "$major_release" -eq 8 ]
    then
        cat << EOF > /etc/yum.repos.d/epel.repo
[epel]
name=Extra Packages for Enterprise Linux 8 - \$basearch
baseurl=https://mirrors.aliyun.com/epel/8/Everything/\$basearch
        http://mirrors.cloud.aliyuncs.com/epel/8/Everything/\$basearch
failovermethod=priority
enabled=1
gpgcheck=0
EOF
    else    
        echo "failed to get os major release"
        out=$(cat /etc/os-release)
        report_error_in_jsonfile "get major release error" 103 "$out"
        exit 1
    fi
}

# config anolis migration repo
migration_repo_config() {
    yum clean all
    rm -rf /etc/yum.repos.d/alinux-migration.repo /etc/yum.repos.d/anolis-migration.repo
    curl "$mirror_site/anolis/migration/anolis-migration.repo" -o /etc/yum.repos.d/anolis-migration.repo || {
        echo "failed to get migration repo"
        out=$(cat /etc/system-release)
	    report_error_in_jsonfile "get migration repo" 103 "$out"
        exit 1
    }
    sed -i "s|https://mirrors.openanolis.cn|$mirror_site|"  /etc/yum.repos.d/anolis-migration.repo
}

install_7to7() {
    out=$(yum -y install centos2anolis-*.an7.noarch --enablerepo=migration 2>&1)
    exit_code=$?
    if [ "$exit_code" -ne 0 ]
    then
        echo "failed to install centos7toanolis7"
        out+="\n$(ls /etc/yum.repos.d)"
        out+="\n$(cat /etc/yum.conf|grep '='|grep -v '#')"
        report_error_in_jsonfile "install centos7toanolis7" 103 "$out"
        exit 1
    fi
    disable_migration_repo
}

install_8to8() {
    out=$(yum -y install centos2anolis-*.an8.noarch --enablerepo=migration 2>&1)
    exit_code=$?
    if [ "$exit_code" -ne 0 ]
    then
        echo "failed to install centos8toanolis8"
        out+="\n$(ls /etc/yum.repos.d)"
        out+="\n$(cat /etc/yum.conf|grep '='|grep -v '#')"
        report_error_in_jsonfile "install centos8toanolis8" 103 "$out"
        exit 1
    fi
    disable_migration_repo
}

install_7to8() {
    sed -i 's|$releasever|7|g' /etc/yum.repos.d/anolis-migration.repo
    yum install -y python-pip
    yum remove -y python-requests python-urllib3
    /usr/bin/pip2 uninstall requests urllib3 -y 2>/dev/null
    out=$(yum -y install leapp --enablerepo=migration 2>&1)
    exit_code=$?
    if [ "$exit_code" -ne 0 ]
    then
        echo "failed to install leapp"
        out+="\n$(ls /etc/yum.repos.d)"
        out+="\n$(cat /etc/yum.conf|grep '='|grep -v '#')"
        # out+="\n$(cat /etc/yum.conf | grep exclude )"
        report_error_in_jsonfile "install leapp" 103 "$out"
        exit 1
    fi
    disable_migration_repo
    
    echo 'epel-release' >> /etc/leapp/transaction/to_remove
    echo 'anolis-release' >> /etc/leapp/transaction/to_remove
    echo 'epel-aliyuncs-release' >> /etc/leapp/transaction/to_install
    echo 'anolis-release-aliyuncs' >> /etc/leapp/transaction/to_install

    sed -i "s|https://mirrors.openanolis.cn|$mirror_site|" /etc/leapp/files/leapp_upgrade_repositories.repo
    sed -i "/BaseOS\/\$basearch\/os/a exclude=anolis-release" /etc/leapp/files/leapp_upgrade_repositories.repo
    cat << EOF >> /etc/leapp/files/leapp_upgrade_repositories.repo

[migration-aliyuncs]
name=Anolis OS - migration repo
baseurl=http://mirrors.cloud.aliyuncs.com/anolis/migration/8/\$basearch/os/
failovermethod=priority
enabled=1
gpgcheck=1
gpgkey=http://mirrors.cloud.aliyuncs.com/anolis/RPM-GPG-KEY-ANOLIS
EOF
}

main() {
    [ x"$1" = "x7to7" ] || [ x"$1" = "x7to8" ] || [ x"$1" = "x8to8" ] || {
        echo "please run command: $0 7to7, $0 8to8, or $0 7to8"
        exit 1 
    }
    case $1 in
        7to7) jsonfile="/var/log/centostoanolis.json";rm -rf $jsonfile;;
        8to8) jsonfile="/var/log/centostoanolis.json";rm -rf $jsonfile;;
        7to8) jsonfile="/var/tmp/state.json";rm -rf $jsonfile;;
    esac
    check_if_centos_or_rhel
    disable_yum_exclude
    epel_repo_config
    migration_repo_config
    case $1 in
        7to7) install_7to7;;
        8to8) install_8to8;;
        7to8) install_7to8;;
    esac
}


main $@
exit_code=$?
[ "$exit_code" -eq 0 ] || exit $exit_code

# workaround for aliyun ecs epel setup
mkdir -p /etc/yum.repos.d/bak && mv /etc/yum.repos.d/*epel* /etc/yum.repos.d/bak/


