#!/bin/bash

npm install -g aws-cdk

python3 -m venv .venv

case "$OSTYPE" in
  darwin*)  source .venv/bin/activate ;; 
  linux*)   source .venv/bin/activate ;;
  msys*)    .venv\Scripts\activate.bat ;;
  cygwin*)  .venv\Scripts\activate.bat ;;
  *)        echo "unknown: $OSTYPE" ;;
esac

pip3 install -r requirements.txt

cdk bootstrap

cdk destroy --force

cdk deploy
