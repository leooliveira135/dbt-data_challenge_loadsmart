# 🌞 dbt-data_challenge_loadsmart

![generated](https://img.shields.io/badge/README-Generated-A931EC?style=flat-square)
![infra](https://img.shields.io/badge/Infrastructure-Terraform-A931EC?style=flat-square)
![aws](https://img.shields.io/badge/AWS-Athena%20%7C%20Glue-A931EC?style=flat-square)
![dbt](https://img.shields.io/badge/dbt-Core%20%7C%20Athena-A931EC?style=flat-square)
![python](https://img.shields.io/badge/Python-3.11-A931EC?style=flat-square)

---

## 🌞 Overview

This repository contains an end-to-end data engineering pipeline using:

- **Terraform** to provision AWS infrastructure  
- **AWS Glue**, **Athena**, **S3**, and **IAM**  
- **dbt Core** + **dbt-athena(-community)**  
- A **Python loader** built with PySpark  
- A complete **Bootstrap script (`setup.sh`)** for Fedora-based systems

The README below reflects the exact logic of `setup.sh`, translated, cleaned up, and organized in a developer-friendly format.

---

## 🌞 Table of Contents

- [Overview](#-overview)  
- [Prerequisites](#-prerequisites)  
- [Quick Setup (Automated Script)](#-quick-setup-automated-script)  
- [Detailed Step-by-Step Guide](#-detailed-step-by-step-guide)  
- [dbt Project Setup](#-dbt-project-setup)  
- [Useful Commands](#-useful-commands)  
- [Notes & Important Considerations](#-notes--important-considerations)  
- [Troubleshooting](#-troubleshooting)  
- [Contributing](#-contributing)  
- [License](#-license)

---

## 🌞 Prerequisites

- Fedora-based Linux distribution  
- Admin/sudo privileges  
- AWS account with permission to create infrastructure  
- Terraform installed (or allow script to install it)  
- Python 3.11 environment (script sets up via pyenv)

---

## 🌞 Quick Setup (Automated Script)

This is the **exact shell script logic**, translated from your `setup.sh`.  
Just update `project_path` and run:

```bash
project_path='/path/to/dbt-data_challenge_loadsmart'

chmod 744 *.sh

# --- Java (Fedora) ---
sudo dnf install -y java-21-openjdk java-21-openjdk-devel
sudo alternatives --config java
export JAVA_BIN=$(readlink -f $(which java))
export JAVA_HOME="$(dirname "$(dirname "$JAVA_BIN")")"
export PATH="$JAVA_HOME/bin:$PATH"
java --version

if type -p java; then echo "Java found"; else echo "Java missing"; exit 1; fi

# --- Terraform ---
sudo dnf install -y dnf-plugins-core
sudo dnf config-manager addrepo --from-repofile=https://rpm.releases.hashicorp.com/fedora/hashicorp.repo
sudo dnf -y install terraform
terraform --help

# --- Infrastructure ---
cd $project_path/terraform
terraform init
terraform plan
terraform apply

# --- AWS CLI ---
cd /tmp
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version

# --- Configure AWS CLI from Terraform outputs ---
cd $project_path/terraform
AWS_KEY=$(terraform output -json credentials | jq -r '.["terraform-aws"].key')
AWS_SECRET=$(terraform output -json credentials | jq -r '.["terraform-aws"].secret')

aws configure set aws_access_key_id $AWS_KEY
aws configure set aws_secret_access_key $AWS_SECRET
aws configure set default.region us-east-1
aws configure set default.output json

aws sts get-caller-identity

# --- pyenv / Python 3.11 ---
curl https://pyenv.run | bash
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv.init -)"
eval "$(pyenv virtualenv-init -)"

pyenv install 3.11.6
pyenv virtualenv 3.11.6 dbt_env
pyenv activate dbt_env

sudo dnf install -y bzip2-devel sqlite-devel readline-devel gdbm-devel libdb-devel libuuid-devel tk-devel

# --- Install dbt ---
sudo dnf install -y python3 python3-pip
pip3 install dbt-core dbt-athena dbt-athena-community
dbt --version

cd $project_path

# --- Init dbt project ---
dbt init

# --- Validate / Build / Test ---
dbt debug --profiles-dir .
dbt run --profiles-dir .
dbt test --profiles-dir .

# --- Loader ---
pip3 install -r $project_path/src/loader/requirements.txt
python -m src.loader.load_data_challenge

echo "Setup completed successfully."
```

---

## 🌞 Detailed Step-by-Step Guide

### 1. Set the project path  

```bash
project_path='/your/local/path'
```

### 2. Make all `.sh` files executable

```bash
chmod 744 *.sh
```

### 3. Install Java 21

(Comments mention Java 11, but script installs Java 21)

```bash
sudo dnf install -y java-21-openjdk java-21-openjdk-devel
sudo alternatives --config java
```

### 4. Install Terraform  
Follow the HashiCorp repo instructions.

### 5. Build AWS Infrastructure  

```bash
terraform init
terraform apply
```

### 6. Install AWS CLI v2  

### 7. Configure AWS CLI using Terraform outputs  

Uses `jq` to parse JSON into AWS credentials.

### 8. Install & Configure pyenv + Python 3.11  

### 9. Install dbt Core + Athena adapter  

### 10. Initialize dbt Project  

During `dbt init`, choose Athena and enter:  
- STG bucket → `s3://data-challenge-loadsmart-stg/athena/`  
- PROD bucket → `s3://data-challenge-loadsmart/athena/`  
- Region → `us-east-1`  
- Schema → `loadsmart`  
- Database → `aws_star_schema`  

### 11. Run loader  

```bash
python -m src.loader.load_data_challenge
```

---

## 🌞 Useful Commands

| Action | Command |
|--------|---------|
| Destroy infra | `terraform destroy` |
| Show Terraform JSON | `terraform output -json | jq .` |
| Activate pyenv | `pyenv activate dbt_env` |
| Test dbt connection | `dbt debug --profiles-dir .` |

---

## 🌞 Notes & Important Considerations

- Script assumes **Fedora**. For Ubuntu/Debian change package manager.  
- Java version mismatch in comments.  
- Terraform outputs include IAM credentials — handle safely.  
- Ensure `jq` is installed.  
- Fix typo: script uses `dnf5`; correct command is `dnf`.

---

## 🌞 Troubleshooting

- **Athena not listed in dbt** → reinstall `dbt-athena-community`  
- **Glue access denied** → IAM or region mismatch  
- **readmeai segmentation fault** → avoid problematic flags; this README is pre-generated  

---

## 🌞 Contributing

1. Fork  
2. Create feature branch  
3. Submit PR  

---

## 🌞 License

No license included yet.
