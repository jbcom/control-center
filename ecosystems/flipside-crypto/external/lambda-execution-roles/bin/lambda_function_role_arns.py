#!/usr/bin/env python3

import os
import time
import sys
import boto3
import json
from base64 import b64encode

inp = json.load(sys.stdin)
execution_role_arn = inp.get("execution_role_arn")

if execution_role_arn:
    sts = boto3.client("sts")

    credentials = sts.assume_role(
        RoleArn=execution_role_arn, RoleSessionName="lambda-function-role-arns"
    )["Credentials"]

    client = boto3.client(
        "lambda",
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )
else:
    client = boto3.client("lambda")


def list_functions(marker):
    if marker is not None:
        response = client.list_functions(Marker=marker)
    else:
        response = client.list_functions()

    return response


def main():
    flist = []
    marker = None
    out = list_functions(marker)

    if "NextMarker" in out:
        marker = out["NextMarker"]
    else:
        marker = None

    for i in out["Functions"]:
        flist.append(i["FunctionName"])

    while marker is not None:
        if "==" in marker:
            out = list_functions(marker)
            if "NextMarker" in out:
                marker = out["NextMarker"]
            else:
                marker = None

            for i in out["Functions"]:
                flist.append(i["FunctionName"])
        else:
            marker = None

    roles = {}

    for fname in flist:
        roles[fname] = client.get_function_configuration(FunctionName=fname)["Role"]

    result = {"roles": b64encode(json.dumps(roles).encode("utf-8")).decode("utf-8")}

    sys.stdout.write(json.dumps(result))


if __name__ == "__main__":
    main()
