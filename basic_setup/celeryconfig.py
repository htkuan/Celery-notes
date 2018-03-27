"""
To verify that your configuration file works properly and doesn’t
contain any syntax errors, you can try to import it:
$ python -m celeryconfig
"""
broker_url = 'amqp://celeryman:pass1234@localhost:5672/celery_vhost'
result_backend = 'redis://localhost:6379/'

accept_content = ['json']
task_serializer = 'json'
result_serializer = 'json'
