#!/usr/bin/env python3

'''
auto-scaling-create-configuration.py

Created by MS.Seo on 2022-12-31.
'''

import argparse

import boto3

import settings
import ec2_utils

parser = argparse.ArgumentParser(description='args parser')
parser.add_argument('instance_name')
parser.add_argument('-t', '--instancetype',
    default=settings.DEFAULT_AUTOSCALING_INSTANCE_TYPE,
    help='The instance type of the EC2 instance')
parser.add_argument('-s', '--securitygroups',
    type=list,
    nargs='+',
    default=settings.DEFAULT_AUTOSCALING_SECURITY_GROUPS,
    help='One or more security groups with which to associate the instances')
parser.add_argument('-k', '--keyname',
    default=settings.DEFAULT_AUTOSCALING_KEY_NAME,
    help='The desired key pair of the Auto Scaling group instances')
parser.add_argument('-i', '--iamrole',
    default=settings.DEFAULT_AUTOSCALING_IAM_ROLE,
    help='The IAM instance profile of the Auto Scaling group instances')
parser.add_argument('--with-instance-monitoring',
    default=False,
    dest='monitoring',
    action='store_true',
    help='Enable EC2 instance detailed(1-minute frequency) monitoring within CloudWatch')
args = parser.parse_args()

ec2 = boto3.client('ec2')

# Find the instance with the name
instances_ids = ec2_utils.find_instances_ids_by_name(args.instance_name)
if not instances_ids:
    raise Exception('Instance not found with name: {}'.format(args.instance_name))
print('Found EC2 instance with name: {}'.format(args.instance_name))

instances_id = instances_ids[0]

image_name = ec2_utils.create_image_name(args.instance_name)
print('Will create image: {}'.format(image_name))

# Create image by the instance
response = ec2.create_image(InstanceId=instances_id, Name=image_name)
image_id = response['ImageId']
print('Creating id: {} name: {}'.format(image_id, image_name))

# Wait for image creation complete
image = ec2_utils.wait_image_creation(image_id)
print('Created id: {} name: {}'.format(image_id, image_name))

# Create autoacaling launch configuration
autoscaling = boto3.client('autoscaling')
response = autoscaling.create_launch_configuration(
    LaunchConfigurationName=image_name,
    KeyName=args.keyname,
    ImageId=image_id,
    InstanceType=args.instancetype,
    SecurityGroups=args.securitygroups,
    InstanceMonitoring={'Enabled': True} if args.monitoring else {'Enabled': False},
    IamInstanceProfile=args.iamrole
)
print('Created launch configuration {} using AMI: {}'.format(image_name, image_id))
