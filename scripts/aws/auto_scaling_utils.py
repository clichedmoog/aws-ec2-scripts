'''
auto_scaling_utils.py

Created by MS.Seo on 2022-12-31.
'''

import socket
import time

import boto3

import settings

autoscaling = boto3.client('autoscaling')
elbv2 = boto3.client('elbv2')

def wait_instances_healthy(autoscaling_group_name):
    healthy_grace_seconds = 10
    
    while True:
        response = autoscaling.describe_auto_scaling_groups(
            AutoScalingGroupNames=[autoscaling_group_name]
        )
        autoscaling_group = response.get('AutoScalingGroups')[0]
        desired_capacity = autoscaling_group.get('DesiredCapacity')
        # ALB with Auto Scaling group
        if autoscaling_group.get('TargetGroupARNs'):
            target_group_arn = autoscaling_group.get('TargetGroupARNs')[0]
            response = elbv2.describe_target_health(
                TargetGroupArn=target_group_arn
            )

            healty_instances = [t['Target']['Id'] for t in response.get('TargetHealthDescriptions') if t['TargetHealth']['State'] == 'healthy']
        # No ELB asssocated with Auto Scaling group
        else:
            healty_instances = [i['InstanceId'] for i in autoscaling_group.get('Instances') if i['HealthStatus'] == 'Healthy']

        # Wait until healthy instances count >= desired_capacity
        if len(healty_instances) >= desired_capacity:
            # Wait health check healthy status valid also for Auto Scaling group 
            time.sleep(healthy_grace_seconds)
            break

        time.sleep(settings.OPERATION_LOOP_INTERVAL)


def wait_instances_draining(autoscaling_group_name):
    while True:
        response = autoscaling.describe_auto_scaling_groups(
            AutoScalingGroupNames=[autoscaling_group_name]
        )
        autoscaling_group = response.get('AutoScalingGroups')[0]
        desired_capacity = autoscaling_group.get('DesiredCapacity')
        # ALB with Auto Scaling group
        if autoscaling_group.get('TargetGroupARNs'):
            target_group_arn = autoscaling_group.get('TargetGroupARNs')[0]

            response = elbv2.describe_target_health(
                TargetGroupArn=target_group_arn
            )

            healty_instances = [t['Target']['Id'] for t in response.get('TargetHealthDescriptions') if t['TargetHealth']['State'] == 'healthy']
            draining_instances = [t['Target']['Id'] for t in response.get('TargetHealthDescriptions') if t['TargetHealth']['State'] == 'draining']

        # No ELB asssocated with Auto Scaling group
        else:
            healty_instances = [i['InstanceId'] for i in autoscaling_group.get('Instances') if i['HealthStatus'] == 'Healthy']
            draining_instances = []

        # Wait until healthy instances count >= desired_capacity and no draining instances
        if len(healty_instances) == desired_capacity and \
            len(draining_instances) == 0:
            break

        time.sleep(settings.OPERATION_LOOP_INTERVAL)


def wait_instances_refreshing(autoscaling_group_name):
    while True:
        response = autoscaling.describe_instance_refreshes(
            AutoScalingGroupName=autoscaling_group_name
        )

        if response.get('InstanceRefreshes'):
            refresh = response.get('InstanceRefreshes')[0]
            if refresh.get('Status') == 'Successful' or refresh.get('Status') == 'Cancelled':
                break

        time.sleep(settings.OPERATION_LOOP_INTERVAL)
