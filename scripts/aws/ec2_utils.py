'''
ec2_utils.py

Created by MS.Seo on 2022-12-31.
'''

import datetime
import socket
import time

import boto3

ec2 = boto3.client('ec2')

def find_instances_by_name(instance_name):
    instances = []
    response = ec2.describe_instances(Filters=[{'Name':'tag:Name', 'Values':[instance_name]}])
    if response['Reservations']:
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append(instance)

    else:
        return []

    return instances


def find_instances_ids_by_name(instance_name):
    instances = find_instances_by_name(instance_name)
    return [instance['InstanceId'] for instance in instances]


def describe_instance_by_id(instance_id):
    instances = []
    response = ec2.describe_instances(Filters=[{'Name':'instance-id', 'Values':[instance_id]}])
    if response['Reservations']:
        for reservation in response['Reservations']:
            for instance in reservation['Instances']:
                instances.append(instance)

    else:
        return None

    return instances[0]


def find_images_by_name(image_name):
    response = ec2.describe_images(Filters=[{'Name':'name', 'Values':[image_name]}])
    if response['Images']:
        return response['Images']
    else:
        return None


def find_image_by_id(image_id):
    response = ec2.describe_images(Filters=[{'Name':'image-id', 'Values':[image_id]}])
    if response['Images']:
        return response['Images'][0]
    else:
        return None


def create_image_name(instance_name):
    '''
    Create image name fotmatted INSTANCENAME-YYMMDD-01
    '''
    # Find the latest image today(UTC)
    date = datetime.datetime.utcnow().date()
    date_str = date.strftime('%y%m%d')
    num = 1

    # Find images createed today by instance_name
    while True:
        image_name = '%s-%s-%02d'%(date_str, instance_name, num)
        if find_images_by_name(image_name):
            num+=1
        else:
            break
    
    return image_name


def wait_instances_state_change(instance_ids):
    while True:
        #print('Wait for instances state change complete')
        found = False
        for instance_id in instance_ids:
            response = describe_instance_by_id(instance_id)
            #print('Instance:%s State:%s'%(response['InstanceId'], response['State']['Name']))
            if response['State']['Name'] == 'shutting-down' or response['State']['Name'] == 'terminated':
                raise Exception('Instance cannot be started: %s'%response['InstanceId'])
            elif response['State']['Name'] == 'stopping' or response['State']['Name'] == 'pending' or response['State']['Name'] == 'rebooting':
                found = True
                break
            else: # running stopped
                pass
        if found:
            time.sleep(5)
            continue
        else:
            break


def start_wait_instances(instance_ids):
    ip_addresses = []
    # wait for instances state change complete
    wait_instances_state_change(instance_ids)

    # start instances & wait for the running state
    response = ec2.start_instances(InstanceIds=instance_ids, DryRun=False)
    while True:
        found = False
        for instance_id in instance_ids:
            response = describe_instance_by_id(instance_id)
            if not response['State']['Name'] == 'running':
                found = True
                break
        if found:
            #print('Wait for instances state running')
            time.sleep(5)
            continue
        else:
            #print('Instances start complete')
            for instance_id in instance_ids: 
                response = describe_instance_by_id(instance_id)
                ip_addresses.append(response['PublicIpAddress'])
            break

    # wait for all instance accessable
    while True:
        found = False
        for ip_address in ip_addresses:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((ip_address, 22))
            except socket.error as e:
                found = True
                break
            s.close()
        if found:
            #print('Wait for instances reachable')
            time.sleep(5)
            continue
        else:
            #print('Instances reachable')
            break

    return ip_addresses


def stop_wait_instances(instance_ids):
    ip_addresses = []

    # wait for instances state change complete
    wait_instances_state_change(instance_ids)

    # start instances & wait for the running state
    response = ec2.stop_instances(InstanceIds=instance_ids, DryRun=False)
    while True:
        found = False
        for instance_id in instance_ids:
            response = describe_instance_by_id(instance_id)
            if not response['State']['Name'] == 'stopped':
                found = True
                break
        if found:
            #print('Wait for instances state stopped')
            time.sleep(5)
            continue
        else:
            #print('Instances stop complete')
            break


def wait_image_creation(image_id):
    while True:
        #print('Wait for image created : %s'%image_id)
        image = find_image_by_id(image_id)

        if image and image['State'] == 'available':
            return image

        time.sleep(5)
