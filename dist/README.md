# 用法

## 制作离线安装包

```bash
chmod +x make_offline_dist.sh
./make_offline_dist.sh
```

分别在 x86_64, aarch64 环境运行上述命令将会在本目录制作离线安装包，包名：anolis_migration_pkgs_x86_64.tar.gz , anolis_migration_pkgs_aarch64.tar.gz

## 使用离线安装包

```bash
# 解压
tar -zxvf anolis_migration_pkgs_`uname -m`.tar.gz

# 安装rpm
cd pkgs
yum install -y python-pip
yum remove -y python-requests python-urllib3; /usr/bin/pip2 uninstall requests urllib3 -y 2>/dev/null || echo "not installed"
yum install -y *.rpm rear genisoimage syslinux nfs-utils python3 wget

# 安装备份工具
cp migrear /usr/sbin/migrear
chmod +x /usr/sbin/migrear
```
