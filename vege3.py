from __future__ import absolute_import
from celery import Celery

app = Celery('routing')  # 建立一個Celery的instance


# celery的相關參數設定
class Config:
    broker_url = 'amqp://celeryman:pass1234@localhost:5672/celery_vhost'
    result_backend = 'redis://localhost:6379/'
    timezone = 'Asia/Taipei'
    task_routes = {'vege3.hello': {'queue': 'queue1'},
                   'vege3.add': {'queue': 'queue2'}}


app.config_from_object(Config)  # 載入設定


# 在實例中加入task
@app.task
def hello(name='world'):
    return f'hello {name}'


@app.task
def add(x, y):
    return x + y


if __name__ == '__main__':
    app.start()
