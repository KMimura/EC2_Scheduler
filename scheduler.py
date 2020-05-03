import boto3;
import datetime;

def lambda_handler(event, context):
    client = boto3.client('ec2', 'ap-northeast-1')
    response = client.describe_instances()
    instance_list = extract_instance_info(response)
    manage_instances(instance_list,client)
    
def extract_instance_info(response):
    return_val = []
    for instance_data in response['Reservations']:
        instance = instance_data['Instances'][0]
        try:
            tmp = {}
            tmp['id'] = instance['InstanceId']
            tmp['start_time'] = convert_time([tag['Value'] for tag in instance['Tags'] if tag['Key'] == 'start-time'][0])
            tmp['stop_time'] = convert_time([tag['Value'] for tag in instance['Tags'] if tag['Key'] == 'stop-time'][0])
            tmp['start_time_holiday'] = convert_time([tag['Value'] for tag in instance['Tags'] if tag['Key'] == 'start-time-holiday'][0])
            tmp['stop_time_holiday'] = convert_time([tag['Value'] for tag in instance['Tags'] if tag['Key'] == 'stop-time-holiday'][0])
            tmp['status'] = instance['State']['Name']
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
    for instance in instance_list:
        required_action = get_required_action(instance)
        if required_action == "start":
            response = client.start_instances(
                InstanceIds=[
                    instance['id']
                ]
            )
            print(response)
        elif required_action == "stop":
            response = client.stop_instances(
                InstanceIds=[
                    instance['id']
                ]
            )
            print(response)

def get_required_action(instance):
    if_holiday = False
    if datetime.datetime.now().weekday() >= 5:
        if_holiday = True
    required_action = "nothing"
    current_time = datetime.datetime.now().time()

    start_time = instance['start_time']
    stop_time = instance['stop_time']
    if if_holiday:
        start_time = instance["start_time_holiday"]
        stop_time = instance["stop_time_holiday"]

    if start_time < stop_time:
        if instance['status'] != 'running' and current_time >= start_time:
            # 起動・停止が同一日付内で、インスタンスが上がっているべき時間帯にインスタンスが落ちている場合
            required_action = "start"
        elif instance['status'] == 'running' and current_time >= stop_time:
            # 起動・停止が同一日付内で、インスタンスが落ちているべき時間帯にインスタンスが上がっている場合
            required_action = "stop"
    else:
        if instance['status'] != 'running' and current_time >= start_time:
            # 起動・停止が別の日付内で、インスタンスが上がっているべき時間帯にインスタンスが落ちている場合
            required_action = "start"
        elif instance['status'] == 'running' and current_time >= stop_time and current_time < start_time:
            # 起動・停止が別の日付内で、インスタンスが落ちているべき時間帯にインスタンスが上がっている場合
            required_action = "stop"
    return required_action