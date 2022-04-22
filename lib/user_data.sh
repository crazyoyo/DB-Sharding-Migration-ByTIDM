#!/bin/bash

#install tools
mkdir tidmmigration; cd ./tidmmigration
touch dmmaster dmworker topology.yaml

yum -y install ec2-instance-connect jq sed
curl -s "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip; ./aws/install; rm -Rf aws

curl -s "http://169.254.169.254/latest/meta-data/local-ipv4" > ./dmmaster
echo "{topology_yaml}" > ./topology.yaml

# install tiup and dmctl
su ec2-user <<EOSU
curl --proto '=https' --tlsv1.2 -sSf https://tiup-mirrors.pingcap.com/install.sh | sh
source /home/ec2-user/.bash_profile
tiup install dm dmctl
EOSU

# generate key for loginless ssh
ssh-keygen -t rsa -f /tidmmigration/tidm_key -q -N ""
chown -R ec2-user:ec2-user /tidmmigration

region=`curl -s http://169.254.169.254/latest/dynamic/instance-identity/document | jq .region -r`

aws ec2 describe-instances \
--region $region \
--filters "Name=tag-value,Values={instanceName}" \
--query 'Reservations[*].Instances[*].[InstanceId]' \
--output text > ./instances

cat ./instances | while read instance
do
	az=`aws ec2 describe-instances \
--region $region \
--filters "Name=instance-id,Values=$instance" \
--query 'Reservations[*].Instances[*].{AZ:Placement.AvailabilityZone}' \
--output text`

	aws ec2-instance-connect send-ssh-public-key \
--region $region \
--instance-id $instance \
--availability-zone $az \
--instance-os-user ec2-user \
--ssh-public-key file:///tidmmigration/tidm_key.pub

	ip=`aws ec2 describe-instances \
--region $region \
--filters \
"Name=instance-id,Values=$instance" \
--query 'Reservations[*].Instances[*].[PrivateIpAddress]' \
--output text`

su ec2-user <<EOSU
		scp -i /tidmmigration/tidm_key -o "StrictHostKeyChecking=no" /tidmmigration/tidm_key.pub $ip:/home/ec2-user/.ssh/
		ssh -i /tidmmigration/tidm_key -o "StrictHostKeyChecking=no" $ip \
		"cat /home/ec2-user/.ssh/tidm_key.pub >> /home/ec2-user/.ssh/authorized_keys" \
		< /dev/null
EOSU

	if [ `cat ./dmmaster` = $ip ]
	then
		sed -i "s/{master_server}/$ip/" ./topology.yaml
		sed -i "s/{monitoring_server}/$ip/" ./topology.yaml
		sed -i "s/{grafana_server}/$ip/" ./topology.yaml
		sed -i "s/{alertmanager_servers}/$ip/" ./topology.yaml
	else
		echo "$ip" >> ./dmworker
	fi
done

num=0
cat ./dmworker | while read workerip
do
	sed -i "s/{worker_server$num}/$workerip/" ./topology.yaml
	num=`expr $num + 1`
done

# open all traffic among whole secuity group
instanceId=`curl "http://169.254.169.254/latest/meta-data/instance-id"`
secGroupId=`aws ec2 describe-instances \
--region $region \
--instance-id $instanceId \
--query "Reservations[].Instances[].SecurityGroups[].GroupId[]" \
--output text`
aws ec2 authorize-security-group-ingress \
    --group-id $secGroupId \
    --protocol -1 \
    --source-group $secGroupId

chown -R ec2-user:ec2-user /tidmmigration

# deploy dm
su - ec2-user <<EOSU
tiup dm deploy {dm_name} {dm_version} /tidmmigration/topology.yaml \
--user ec2-user -i /tidmmigration/tidm_key -y

tiup dm start {dm_name}
EOSU