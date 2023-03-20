#!/usr/bin/env python3
'''
auto-scaling-adjust.py

Created by MS.Seo on 2022-12-31.
'''

import argparse

import boto3

import settings
import utils


parser = argparse.ArgumentParser(description='args parser')
parser.add_argument('autoscaling_group_name')
parser.add_argument('--minsize',
	metavar='N',
    type=int,
    help='The minimum size of the Auto Scaling group')
parser.add_argument('--maxsize',
	metavar='N',
    type=int,
    help='The maximum size of the Auto Scaling group')
parser.add_argument('--capacity',
    type=int,
    help='The desired capacity of the Auto Scaling group')
args = parser.parse_args()

# Find the lastest autoacaling launch configurationby hostname
autoscaling_client = boto3.client('autoscaling')

kwargs = {'AutoScalingGroupName': args.autoscaling_group_name}
if args.minsize:
	kwargs['MinSize'] = args.minsize
if args.maxsize:
	kwargs['MaxSize'] = args.maxsize
if args.capacity:
	kwargs['DesiredCapacity'] = args.capacity

response = autoscaling_client.update_auto_scaling_group(**kwargs)
if utils.response_success(response):
	print('Applied settings')