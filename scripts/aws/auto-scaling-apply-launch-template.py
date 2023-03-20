#!/usr/bin/env python3
'''
auto-scaling-apply-launch-template.py

Created by MS.Seo on 2022-12-31.
'''

import argparse

import boto3

import auto_scaling_utils


parser = argparse.ArgumentParser(description='args parser')
parser.add_argument('autoscaling_group_name',
    help='Auto Scaling group name')
parser.add_argument('-v', '--version',
    type=int,
    default=None,
    help='Luanch template version to apply (latest if not set)')

args = parser.parse_args()
version = str(args.version) if args.version else '$Latest'
print('Applying new version:{} on auto scaling group: {} ...'.format(version, args.autoscaling_group_name))

# Prepare clients
ec2 = boto3.client('ec2')
autoscaling = boto3.client('autoscaling')

# Check no instance refreshs progressing
response = autoscaling.describe_instance_refreshes(
    AutoScalingGroupName=args.autoscaling_group_name
)
if response.get('InstanceRefreshes'):
    refresh = response.get('InstanceRefreshes')[0]
    if refresh.get('Status') != 'Successful' and refresh.get('Status') != 'Cancelled':
        raise Exception('Found instance refresh in progress')

# Check Auto Scaling group & launch configuration information
response = autoscaling.describe_auto_scaling_groups(
    AutoScalingGroupNames=[args.autoscaling_group_name]
)
if not response.get('AutoScalingGroups'):
    raise Exception('Auto Scaling group not found')

autoscaling_group = response.get('AutoScalingGroups')[0]
instances = autoscaling_group.get('Instances')
group_min_size = autoscaling_group.get('MinSize')
group_max_size = autoscaling_group.get('MaxSize')
group_capacity = autoscaling_group.get('DesiredCapacity')

if not autoscaling_group.get('MixedInstancesPolicy'):
    raise Exception('Auto Scaling group not using launch template')

if group_max_size < group_capacity * 2:
    raise Exception('Auto Scaling group max size should be capacity * 2 for apply')

launch_template_name = autoscaling_group['MixedInstancesPolicy']['LaunchTemplate']['LaunchTemplateSpecification']['LaunchTemplateName']

# Change new template version as default
print('Update launch template {} default version {}'.format(launch_template_name, version))
response = ec2.modify_launch_template(
    LaunchTemplateName=launch_template_name,
    DefaultVersion=version
)

# Increase Auto Scaling group capacity by x2 and wait healthy
print('Increase Auto Scaling group size & capacity {}'.format(min(group_max_size, (group_capacity * 2))))
response = autoscaling.update_auto_scaling_group(
    AutoScalingGroupName=args.autoscaling_group_name,
    MinSize=(group_capacity * 2),
    DesiredCapacity=(group_capacity * 2)
)

if group_capacity == 0:
    print('Auto Scaling group has no instances; no need to wait instances with new configuration')
    exit(0)

# Wait for healthy instances with new configuration
print('Waiting Auto Scaling instance with healthy count {}'.format((group_capacity * 2)))
auto_scaling_utils.wait_instances_healthy(args.autoscaling_group_name)

# Revert min_size of autosacleing group
response = autoscaling.update_auto_scaling_group(
    AutoScalingGroupName=args.autoscaling_group_name,
    MinSize=group_min_size,
    DesiredCapacity=group_capacity,
)

# Wait for healthy instances with new configuration
print('Waiting Auto Scaling instance with healthy count {}, draining 0'.format(group_capacity))
auto_scaling_utils.wait_instances_draining(args.autoscaling_group_name)
