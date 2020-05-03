import boto3;
import datetime;

def lambda_handler(event, context):
    client = boto3.client('ec2', 'ap-northeast-1')
    response = client.describe_instances()
    instance_list = extract_instance_info(response)
    manage_instances(instance_list,client)
    
def extract_instance_info(response):
    return_val = []
    for instance_data in response['Reservations'][0]['Instances']:
        try:
            tmp = {}
            tmp['id'] = instance_data['InstanceId']
            tmp['start_time'] = convert_time([tag['Value'] for tag in instance_data['Tags'] if tag['Key'] == 'start-time'][0])
            tmp['stop_time'] = convert_time([tag['Value'] for tag in instance_data['Tags'] if tag['Key'] == 'stop-time'][0])
            tmp['status'] = instance_data['State']['Name']
            return_val.append(tmp)
        except:
            # when the instance is not expected to be started / stopped automatically
            continue
    print(return_val)
    return return_val

def convert_time(str_time):
    hour = int(str_time[:2])
    min = int(str_time[2:4])
    return datetime.time(hour,min)
    
def manage_instances(instance_list,client):
    current_time = datetime.datetime.now().time()
    for instance in instance_list:
        # when the start time and the stop time are set within the same day (i.e. 0600 qand 2300)
        if instance['start_time'] < instance['stop_time']:
            if instance['status'] != 'running' and current_time >= instance['start_time']:
                response = client.start_instances(
                    InstanceIds=[
                        instance['id']
                    ]
                )
                print(response)
            elif instance['status'] == 'running' and current_time >= instance['stop_time']:
                response = client.stop_instances(
                    InstanceIds=[
                        instance['id']
                    ]
                )
                print(response)
            else:
                print('no action was taken')
        else:
            # when the start time and the stop time are set on different days (i.e. 0600 qand 0030)
            if instance['status'] != 'running' and current_time >= instance['start_time']:
                response = client.start_instances(
                    InstanceIds=[
                        instance['id']
                    ]
                )
                print(response)
            elif instance['status'] == 'running' and current_time >= instance['stop_time'] and current_time < instance['start_time']:
                response = client.stop_instances(
                    InstanceIds=[
                        instance['id']
                    ]
                )
                print(response)
            else:
                print('no action was taken')

    