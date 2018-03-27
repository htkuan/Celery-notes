from __future__ import absolute_import
from celery import Celery
from celery.schedules import crontab

app = Celery('beat1')  # 建立一個Celery的instance


# celery的相關參數設定
class Config:
    broker_url = 'amqp://celeryman:pass1234@localhost:5672/celery_vhost'
    result_backend = 'redis://localhost:6379/'
    timezone = 'Asia/Taipei'
    beat_schedule = {
        # 每 10 秒發送這個 hello 這個 task
        'add-every-10-seconds': {
            'task': 'vege1.hello',
            'schedule': 10.0,
            'args': ['my friend']
        },
        # 每分鐘 0 秒時發送 add 這個 task
        'add-every-minute': {
            'task': 'vege1.add',
            'schedule': crontab(minute='*'),
            'args': (5, 10)
        }
    }


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
