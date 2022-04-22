import os
import json
from datetime import datetime
from aws_cdk import (
    Stack,
    aws_iam as _iam,
    aws_ec2 as _ec2
)
from constructs import Construct

class TiDMMigrationStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # get parameters
        with open('./config/config.json') as j:
            cfg = json.load(j)['tidm']

        # get ec2 default vpc
        vpc = _ec2.Vpc.from_lookup(self, "VPC",
            is_default=True
        )

        # create new security group
        sec_group = _ec2.SecurityGroup(
            self,
            "TiDMMigrationSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
        )

        # add a new ingress rule to allow port 22 to internal hosts
        sec_group.add_ingress_rule(
            peer=_ec2.Peer.any_ipv4(),
            description="Allow SSH connection", 
            connection=_ec2.Port.tcp(22)
        )

        # create role for EC2
        ec2_role = _iam.Role(self, "tidm_migration_role",
            role_name = "tidm_migration_role",
            assumed_by=_iam.ServicePrincipal("ec2.amazonaws.com"))

        ec2_role.add_managed_policy(_iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2FullAccess"))
        ec2_role.add_to_policy(_iam.PolicyStatement(
            effect=_iam.Effect.ALLOW,
            resources=["arn:aws:ec2:"+os.environ["CDK_DEFAULT_REGION"]+":"+os.environ["CDK_DEFAULT_ACCOUNT"]+":instance/*"],
            conditions={
                "StringEquals": {
                    "ec2:osuser": "ec2-user"
                }
            },
            actions=["ec2-instance-connect:SendSSHPublicKey"]
        ))

        # AWS Linux 2
        instanceType=cfg["instance_type"]
        instanceName="TiDMMigrationInstance" + datetime.now().strftime("%m%d-%H%M%S")

        with open("./lib/topology-worker.yaml") as w:
            _topologyWorker = w.read()
            _topologyWorker = _topologyWorker.replace("{instanceName}", instanceName)

        _topologyWorkers = ""
        _tmptopologyWorker = _topologyWorker
        for n in range(0, int(cfg["instance_num"]) -1 ):
            _tmptopologyWorker = _tmptopologyWorker.replace("{worker_port}", str(8262+n))
            _tmptopologyWorker = _tmptopologyWorker.replace("{worker_server}", "{worker_server"+str(n)+"}")
            _topologyWorkers = _topologyWorkers + _tmptopologyWorker + "\n"
            _tmptopologyWorker = _topologyWorker

        with open("./lib/topology.yaml") as t:
            _topology = t.read()
            _topology = _topology.replace("{worker_server_placeholder}", _topologyWorkers)
            _topology = _topology.replace('"', '\\"')

        with open("./lib/user_data.sh") as u:
            _user_data = u.read()
            _user_data = _user_data.replace("{instanceName}", instanceName)
            _user_data = _user_data.replace("{dm_name}", cfg["dm_name"])
            _user_data = _user_data.replace("{dm_version}", cfg["dm_version"])
            _user_data = _user_data.replace("{topology_yaml}", _topology)

        # print(_user_data)

        for n in range(0, int(cfg["instance_num"])):
            if n == 0:
                _ec2.Instance(self, 'TiDMInstance{}'.format(str(n).zfill(2)),
                vpc=vpc,
                security_group=sec_group,
                vpc_subnets=_ec2.SubnetSelection(
                    subnet_type=_ec2.SubnetType.PUBLIC
                ),
                instance_type=_ec2.InstanceType(instanceType),
                instance_name=instanceName,
                machine_image=_ec2.AmazonLinuxImage(
                    generation=_ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
                ),
                block_devices=[_ec2.BlockDevice(
                    device_name="/dev/sda1",
                    volume=_ec2.BlockDeviceVolume.ebs(int(cfg["ebs_volumn_size"]))
                )],
                role=ec2_role,
                key_name=cfg["key_pair"],
                user_data=_ec2.UserData.custom(_user_data),
            )
            else:
                _ec2.Instance(self, 'TiDMInstance{}'.format(str(n).zfill(2)),
                vpc=vpc,
                security_group=sec_group,
                vpc_subnets=_ec2.SubnetSelection(
                    subnet_type=_ec2.SubnetType.PUBLIC
                ),
                instance_type=_ec2.InstanceType(instanceType),
                instance_name=instanceName,
                machine_image=_ec2.AmazonLinuxImage(
                    generation=_ec2.AmazonLinuxGeneration.AMAZON_LINUX_2
                ),
                block_devices=[_ec2.BlockDevice(
                    device_name="/dev/sda1",
                    volume=_ec2.BlockDeviceVolume.ebs(int(cfg["ebs_volumn_size"]))
                )],
                role=ec2_role,
                key_name=cfg["key_pair"]
            )

            # _ec2.InitCommand.argvCommand(['powershell.exe',` '-command "Set-ExecutionPolicy', 'RemoteSigned -Force"'], { key: "00_executionPolicy", waitAfterCompletion: ec2.InitCommandWaitDuration.none() }),
