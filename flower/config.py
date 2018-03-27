import os

port = int(os.environ.get('FLOWER_PORT', '5555'))

basic_auth = [os.environ.get('BASIC_AUTH', 'username:password')]
max_tasks = 100000
