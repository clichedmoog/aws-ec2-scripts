'''
settings.py

Created by MS.Seo on 2022-12-31.
'''

# Timeout & check interval in seconds
OPERATION_TIMEOUT = 300
OPERATION_LOOP_INTERVAL = 5

# AutoScaling configuration defaults
DEFAULT_AUTOSCALING_INSTANCE_TYPE = 't4g.micro'
DEFAULT_AUTOSCALING_KEY_NAME = None
DEFAULT_AUTOSCALING_IAM_ROLE = None
DEFAULT_AUTOSCALING_SECURITY_GROUPS = ['']
