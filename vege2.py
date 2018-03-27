from __future__ import absolute_import
from celery import Celery
from celery.schedules import crontab

app = Celery('beat2')  # 建立一個Celery的instance


# celery的相關參數設定
class Config:
    broker_url = 'amqp://celeryman:pass1234@localhost:5672/celery_vhost'
    result_backend = 'redis://localhost:6379/'
    timezone = 'Asia/Taipei'


app.config_from_object(Config)  # 載入設定


# 在實例中加入task
@app.task
def hello(name='world'):
    return f'hello {name}'


@app.task
def add(x, y):
    return x + y


# add periodic task
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls hello('there') every 10 seconds.
    sender.add_periodic_task(10.0,
                             hello.s('there'),
                             name='every 10s',
                             queue='queue1')

    # Executes every Monday morning at 7:30 a.m.
    sender.add_periodic_task(
        crontab(hour=7, minute=30, day_of_week=1),
        add.s(5, 10),
        name='every Monday morning at 7:30 a.m.',
        queue='queue2'
    )


if __name__ == '__main__':
    app.start()
