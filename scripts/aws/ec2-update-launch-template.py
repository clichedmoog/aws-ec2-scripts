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
parser.add_argument('launch_template_name')
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

# Update autoacaling launch template version
response = ec2.create_launch_template_version(
    LaunchTemplateName=args.launch_template_name,
    SourceVersion='$Latest',
    VersionDescription=image_name,
    LaunchTemplateData={
        'ImageId': image_id,
        'IamInstanceProfile': {
            'Name': settings.DEFAULT_AUTOSCALING_IAM_ROLE
        },
        'KeyName': settings.DEFAULT_AUTOSCALING_KEY_NAME
    }
)
launch_template_version = response['LaunchTemplateVersion']['VersionNumber']
print('Updated template {} using AMI: {} as version {}'.format(args.launch_template_name, image_name, launch_template_version))
