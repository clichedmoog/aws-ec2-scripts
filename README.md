# aws-ec2-scripts

Python scripts for updating AWS EC2, Auto Scaling Groups

## Preparation

boto3 package should be installed

```zsh
pip install -r requirements.txt
```

or

```zsh
pip install boto3
```

AWS credentials should be set before running scripts
https://docs.aws.amazon.com/ko_kr/cli/latest/userguide/cli-chap-configure.html

## Run Scripts

Start stopped EC2 instance by name and return an IP address
```zsh
./scripts/aws/ec2-start.py [instance_name]
```

Stop running EC2 instance by name
```zsh
./scripts/aws/ec2-stop.py [instance_name]
```

Update a launch template, create a machine image using an instance
```zsh
./scripts/aws/ec2-update-launch-template.py [instance_name] [launch_template_name]
```

Delete launch template versions
```zsh
./scripts/aws/ec2-delete-launch-template-version.py [launch_template_name] -k [version_count_numbers_to_keep] -d [version_count_numbers_to_delete]
```

Create Auto Scaling configuration, create a machine image using an instance
```zsh
./scripts/aws/auto-scaling-create-configuration.py [instance_name] -t [instance_type] -s [securitygroups] -k [key_name] -i [iam_role]
```

Apply Auto Scaling launch template
```zsh
./scripts/aws/auto-scaling-apply-launch-template.py [auto_scaling_group_name] -v [version_to_apply]
```

Apply Auto Scaling configuration
```zsh
./scripts/aws/auto-scaling-apply-configuration.py [auto_scaling_group_name] [new_configuration_name]
```

Refresh instance for Auto Scaling group
```zsh
./scripts/aws/auto-scaling-refresh-instance.py [auto_scaling_group_name]
```

Adjust Auto Scaling
```zsh
./scripts/aws/auto-scaling-adjust.py [auto_scaling_group_name] --minsize [minimum_size_of_auto_scaling_group] --maxsize [maximum_size_of_auto_scaling_group] --capacity [current_capacity_size_of_auto_scaling_group]
```
