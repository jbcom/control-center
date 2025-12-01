# Secrets

At FlipsideCrypto we use [Mozilla SOPS](https://github.com/mozilla/sops) with AWS customer-managed-keys to encrypt and decrypt the data.

This repository's KMS key is: **arn:aws:kms:us-east-1:862006574860:alias/global**.

SOPS is is an editor of encrypted files that supports YAML, JSON, ENV, INI and BINARY formats.

Secrets are stored in a subdirectory, [secrets](./secrets).

## Setting up your Local Environment for SOPS

You can follow the instructions on the SOPS website for [downloading](https://github.com/mozilla/sops#stable-release) the binary or you can on MacOS or Linux (With LinuxBrew) use the SOPS [Homebrew Formulae](https://formulae.brew.sh/formula/sops).

To run SOPS you will need to be logged into AWS with your SSO credentials.

To do this, first make sure your AWS profile is set correctly.

AWS profiles are setup in your ~/.aws/config file, like so:

```toml
[profile FlipsideCryptoRoot]
sso_start_url = https://flipsidecrypto.awsapps.com/start
sso_region = us-east-1
sso_account_id = 862006574860
sso_role_name = EngineeringAccess
region = us-east-1
```

You will need a profile setup for the **root AWS account**, which is the one demonstrated above.

Once you have a configured AWS profile log into it with:

```bash
aws sso login --profile PROFILE_NAME
```

Where PROFILE_NAME is the name of the AWS profile, like _FlipsideCryptoRoot_, shown above.

You can then tell your terminal session to use that AWS profile by exporting an environment variable, _AWS_PROFILE_, like so:

```shell
export AWS_PROFILE=PROFILE_NAME
```

You can disable the profile when you are done by running:

```shell
unset AWS_PROFILE
```

## Encrypting secrets with SOPS

A configuration file, [.sops.yaml](.sops.yaml), tells SOPS to use the repository KMS key, so as long as you run sops from the directory containing that file (typically the repository root or a Terraform workspace directory), you will not need to specify the encryption key:

```shell
sops -e -i secrets/my-secrets.json
```

This is particularly useful when calling sops from Github Actions, as it eliminates needing to hardcode any keys in your workflow.

You can however call sops from any directory by specifying the repository KMS key directly:

```bash
sops -e -i --kms "arn:aws:kms:us-east-1:862006574860:alias/global" your-secrets.json
```

Note that in both cases the flags _-e_, and _-i_, are shortened forms of _--encrypt_, and _-in-place_, respectively.

Specifying _in-place_ is **very important**, as without it you will not actually encrypt the original file.

**If you submit a pull request with unencrypted secrets you will not only have to resubmit, you will need to regenerate any sensitive data as they are now in Github repository memory in some form. So don't do that.**

## Editing Encrypted Secrets

You can always go back and edit already existing encrypted secrets.

Follow the same procedure for logging into AWS and for setting the KMS key explicitly if not in the repository root directory.

Simply avoid setting either _encrypt_, and _in-place_, instead run SOPS like:

```shell
sops secrets/my-secret.json
```

Which will open a terminal editor with your secret file decrypted, allowing you to edit it.

## Advanced Usage

Mozilla maintains its own set of [examples](https://github.com/mozilla/sops#examples) which cover advanced usage of the sops binary.
