import json
import boto3
import logging
import datetime
from urllib2 import Request
from urllib2 import urlopen

log = logging.getLogger()
log.setLevel(logging.INFO)

log.debug('Loading function')

cw = boto3.client('cloudwatch', region_name='ap-south-1')

# Save the connection status in the CloudWatch Custom Metric
def putCloudWatchMetric(metricName, value, vgw, cgw, region, tunnel0, tunnel1, ip):
    cw.put_metric_data(
        Namespace='MediassistVPNStatus',
        MetricData=[{
            'MetricName': metricName,
            'Value': value,
            'Unit': 'Count',
            'Dimensions': [{
                'Name': 'VGW',
                'Value': vgw
            },
                {
                    'Name': 'CGW',
                    'Value': cgw
                },
                {
                    'Name': 'Region',
                    'Value': region
                },
                {
                    'Name': 'Tunnel0Status',
                    'Value': tunnel0
                },
                {
                    'Name': 'Tunnel1Status',
                    'Value': tunnel1
                },
                {
                    'Name': 'IP',
                    'Value': ip
                }]
        }]
    )


def lambda_handler(event, context):
  
    # Declare variables
    ec2 = boto3.client('ec2')
    AWS_Regions = ec2.describe_regions()['Regions']
    numConnections = 0

    # Check VPN connections status in all the regions
    for region in AWS_Regions:
        try:
            ec2 = boto3.client('ec2', region_name=region['RegionName'])
            awsregion = region['RegionName']
            vpns = ec2.describe_vpn_connections()['VpnConnections']
            connections = 0
            ip = 'xx.xx.xxx.xxx' #IP provided in Customer Gateway
            for vpn in vpns:
                if vpn['State'] == "available":
                    numConnections += 1
                    connections += 1
                    active_tunnels = 0
                    if vpn['VgwTelemetry'][0]['Status'] == "UP":
                        active_tunnels += 1
                    if vpn['VgwTelemetry'][1]['Status'] == "UP":
                        active_tunnels += 1
                    log.info('{} VPN ID: {}, State: {}, Tunnel0: {}, Tunnel1: {} -- {} active tunnels'.format(region['RegionName'], vpn['VpnConnectionId'],vpn['State'],vpn['VgwTelemetry'][0]['Status'],vpn['VgwTelemetry'][1]['Status'], active_tunnels))
                    putCloudWatchMetric(vpn['VpnConnectionId'], active_tunnels, vpn['VpnGatewayId'], vpn['CustomerGatewayId'], region['RegionName'], vpn['VgwTelemetry'][0]['Status'], vpn['VgwTelemetry'][1]['Status'], ip)
        except Exception as e:
            log.error("Exception: "+str(e))
            continue

