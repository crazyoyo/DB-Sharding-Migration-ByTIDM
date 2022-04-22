#!/usr/bin/env python3

import os
from aws_cdk import App
from aws_cdk import Tags
from aws_cdk import Environment

from tidm.migration_stack import TiDMMigrationStack

app = App()
tidmMigStack = TiDMMigrationStack(app, "tidm-migration", 
    env=Environment(
        account=os.environ["CDK_DEFAULT_ACCOUNT"],
        region=os.environ["CDK_DEFAULT_REGION"]
    )
)

app.synth()
