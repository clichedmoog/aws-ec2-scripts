#!/usr/bin/env python3
'''
auto-scaling-apply-configuration.py

Created by MS.Seo on 2022-12-31.
'''

import argparse

import boto3

import auto_scaling_utils


parser = argparse.ArgumentParser(description='args parser')
parser.add_argument('autoscaling_group_name',
    help='The Auto Scaling group name')
parser.add_argument('new_configuration_name',
    help='A new launch congifuration name to apply')

args = parser.parse_args()

print('Applying launch configuration:{} on auto scaling group: {} ...'.format(args.new_configuration_name, args.autoscaling_group_name))

# Prepare clients
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

if not autoscaling_group.get('LaunchConfigurationName'):
    raise Exception('Auto Scaling group not using launch configuration')

if group_max_size < group_capacity * 2:
    raise Exception('Auto Scaling group max size should be capacity * 2 for apply')

configuration_name = autoscaling_group.get('LaunchConfigurationName')

for instance in instances:
    if instance.get('LifecycleState') == 'InService' and \
        instance.get('LaunchConfigurationName') != configuration_name:
        raise Exception('Found not matching launch configurationn name maybe previous appling in progress')

response = autoscaling.describe_launch_configurations(
    LaunchConfigurationNames=[args.new_configuration_name]
)
if not response.get('LaunchConfigurations'):
    raise Exception('Launch configuration {} not found'.format(args.new_configuration_name))

# Change launch config & increase Auto Scaling groups's number of instances by x2 + 4(for extra)
response = autoscaling.update_auto_scaling_group(
    AutoScalingGroupName=args.autoscaling_group_name,
    LaunchConfigurationName=args.new_configuration_name,
    MinSize=(group_capacity * 2),
    DesiredCapacity=(group_capacity * 2),
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
