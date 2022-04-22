# tidb-dm-autodeploy-bycdk
Migrate RDBMS Sharding to Amazon Aurora by TiDB Data Migration

### Prerequisite
1. An IAM user with EC2FullAccess, which should be deleted after CDK deployment.

2. A Linux machine to deploy CDK codes, with aws IAM user's AK/SK configured.

3. NodeJS, Python3, PIP, AWS CLI are installed on the Linux machine.

### To deploy
1. Ensure CDK is installed
```
$ npm install -g aws-cdk
```

2. Create a Python virtual environment
```
$ python3 -m venv .venv
```

3. Activate virtual environment

_On MacOS or Linux_
```
$ source .venv/bin/activate
```

_On Windows_
```
% .venv\Scripts\activate.bat
```

4. Install the required dependencies.

```
$ pip install -r requirements.txt
```

5. Bootstrapping cdk environment.

```
$ cdk bootstrap
```

6. Synthesize (`cdk synth`) or deploy (`cdk deploy`) the example, use --require-approval to run without being prompted for approval.

```
$ cdk deploy --require-approval never
```

### To run
1. ssh to dm-master node, whose ip can be found on AWS CloudFormation console.

2. list and show the DM master.

```
$ tiup dm list
```

```
$ tiup dm display dm-migration
```

### To clean-up:

```
$ cdk destroy
```