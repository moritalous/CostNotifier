import boto3
import datetime
import json
import os

client = boto3.client('ce')

end_day = datetime.datetime.now()
start_day = end_day.replace(day=1)

def get_cost_and_usage_service():
    cost_and_usage = client.get_cost_and_usage(
        TimePeriod={
            'Start': start_day.strftime('%Y-%m-%d'),
            'End': end_day.strftime('%Y-%m-%d')
        },
        Granularity='MONTHLY',
        Metrics=['BLENDED_COST'],
        GroupBy=[{
            'Type': 'DIMENSION',
            'Key': 'SERVICE'
        }]
        )
    
    return cost_and_usage['ResultsByTime'][0]['Groups']
    
    
def format_output(service_cost):
    output = []
    total_cost = 0.00
    total_unit = ''
    
    for service in service_cost:
        service_name = service['Keys'][0]
        blended_cost_amount = float(service['Metrics']['BlendedCost']['Amount'])
        blended_cost_unit = service['Metrics']['BlendedCost']['Unit']
        output.append('{}:\r\n\t\t\t{}{}'.format(service_name, round(blended_cost_amount, 2), blended_cost_unit))
        total_cost = total_cost + blended_cost_amount
        total_unit = blended_cost_unit
    
    output.append('-----')
    output.append('Total:\r\n\t\t\t{}{}'.format(round(total_cost, 2), total_unit))
    
    subject = 'Monthly AWS Cost {}{}'.format(round(total_cost, 2), total_unit)
    return '\r\n'.join(output), subject
    
    
def sns_notify(subject, message):
    sns_client = boto3.client('sns')

    topic_arn = os.environ.get('SNS_TOPIC_ARN', '')
    if topic_arn == '':
        print('ERROR: SNS_TOPIC_ARN is not set.')
        return
    
    sns_client.publish(
        TopicArn = topic_arn,
        Subject = subject,
        Message = message
        )


def lambda_handler(event, context):
    
    service_cost =get_cost_and_usage_service()
    output, subject = format_output(service_cost)
    
    sns_notify(subject, output)

    return {
        'statusCode': 200,
        'body': json.dumps(output)
    }
