#!/usr/bin/env python3

'''
start-ec2.py

Created by MS.Seo on 2022-12-31.
'''

import argparse

import ec2_utils

parser = argparse.ArgumentParser(description='args parser')
parser.add_argument('instance_name', help='Instance name to start')
args = parser.parse_args()

instance_ids = ec2_utils.find_instances_ids_by_name(args.instance_name)
if not instance_ids:
	print('Instances not found')
	exit(-1)
ip_addresses = ec2_utils.start_wait_instances(instance_ids)

for ip_address in ip_addresses:
	print(ip_address)