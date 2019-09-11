import boto3 as AWS

from credentials import AWS_ACCESS_KEY, AWS_SECRET_KEY, USER, TABLE_NAME

class _DynamoDBClient():
    """ Client object to facilitate access to user settings in DynamoDB
    """

    def __init__(self):
        self.client = AWS.client(
            'dynamodb',
            region_name='us-east-1',
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY
        )
        self.table_name = TABLE_NAME
        self.key = {
            'user_id': {
                'S': USER
            }
        }

    def get_record(self):
        return self.client.get_item(TableName=self.table_name, Key=self.key)['Item']

    def update_restart_flag(self):
        updates = {
            'shouldRestart': {
                'Value': {
                    'BOOL': False
                },
                'Action': 'PUT'
            }
        }
        self.client.update_item(
            TableName=self.table_name,
            Key=self.key,
            AttributeUpdates=updates
        )

_dynamoDBClient = _DynamoDBClient()
def DynamoDBClient():
    """A method to effectively make DynamoDBClient a singleton class.

    We want DynamodDBClient to be a singleton because we can use the same client
    for all DynamoDB operations.
    """
    return _dynamoDBClient
