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
parser.add_argument('--percentage', required=False, type=int, choices=range(0,101),
                   metavar="[0-100]", 
                   help='At least this percentage of the desired capacity of the Auto Scaling group must remain healthy during this operation to allow it to continue. Default is 90.', default=90)
parser.add_argument('--warmup', required=False, type=int, choices=range(0,301),
                   metavar="[0-300]", 
                   help='How much time it takes a newly launched instance to be ready to use. Default is 60.', default=60)
args = parser.parse_args()

print('Start instance refresh on auto scaling group: {} ...'.format(args.autoscaling_group_name))

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
response = autoscaling.start_instance_refresh(
    AutoScalingGroupName=args.autoscaling_group_name,
    Strategy='Rolling',
    Preferences={
        'MinHealthyPercentage': args.percentage ,
        'InstanceWarmup': args.warmup
    }
)
# Wait for healthy instances with new configuration
print('Waiting Auto Scaling instance refresh finishes')
auto_scaling_utils.wait_instances_refreshing(args.autoscaling_group_name)
