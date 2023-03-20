#!/usr/bin/env python3

'''
auto-scaling-create-configuration.py

Created by MS.Seo on 2022-12-31.
'''

import argparse

import boto3

import utils

parser = argparse.ArgumentParser(description='args parser')
parser.add_argument('launch_template_name')
parser.add_argument('-k', '--keep',
    metavar='N',
    type=int,
    default=None,
    help='Number of versions to keep from deletion (keep $Default ~ $Latest if 0)')
parser.add_argument('-d', '--delete',
    metavar='VERSION',
    type=int,
    nargs='+',
    default=[],
    help='Verson numbers to delete')


args = parser.parse_args()

ec2 = boto3.client('ec2')

response = ec2.describe_launch_template_versions(
    LaunchTemplateName=args.launch_template_name,
)

if not response.get('LaunchTemplateVersions'):
    raise Exception('No launch template or launch template versions found')
template_versions = [v for v in response.get('LaunchTemplateVersions')]
template_version_numbers = [v['VersionNumber'] for v in response.get('LaunchTemplateVersions')]
default_version = next(v['VersionNumber'] for v in response.get('LaunchTemplateVersions') if v['DefaultVersion'])
print('Found launch template versions {} from {}'.format(template_version_numbers, args.launch_template_name))

deleting_template_version_numbers = []

if args.keep != None:
    if args.keep == 0:
        default_version_index = template_version_numbers.index(default_version)
        deleting_template_version_numbers = template_version_numbers[default_version_index + 1:]
    else:
        deleting_template_version_numbers = deleting_template_version_numbers[-1 * args.keep:]

# Add addional versions
for d in args.delete:
    if d not in deleting_template_version_numbers:
        deleting_template_version_numbers.extend(args.delete)

# Delete launch template version
print('Deleting launch template versions {} from {}'.format(deleting_template_version_numbers, args.launch_template_name))
versions = [str(v) for v in deleting_template_version_numbers]
image_ids = [v['LaunchTemplateData']['ImageId'] for v in template_versions if v['VersionNumber'] in deleting_template_version_numbers]
response = ec2.delete_launch_template_versions(
    LaunchTemplateName=args.launch_template_name,
    Versions=versions,
)
if utils.response_success(response) and image_ids:
    # Get snapshot_ids from image_ids
    response = ec2.describe_images(
        ImageIds=image_ids,
    )
    if not response.get('Images'):
        raise Exception('No images used for template versions found')
    snapshot_ids = [i['BlockDeviceMappings'][0]['Ebs']['SnapshotId'] for i in response['Images']]
    # Delete AMI used for launch template
    for image_id in image_ids:
        print('Deleting image {}'.format(image_id))
        response = ec2.deregister_image(
            ImageId=image_id,
        )
    for snapshot_id in snapshot_ids:
        print('Deleting snapshot {}'.format(snapshot_id))
        response = ec2.delete_snapshot(
            SnapshotId=snapshot_id,
        )

print('Deleted launch template versions {} from {}'.format(deleting_template_version_numbers, args.launch_template_name))
