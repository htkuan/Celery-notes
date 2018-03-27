from __future__ import absolute_import
from celery import Celery
from celery import group, chain, chord, chunks

app = Celery('work-flow')  # 建立一個Celery的instance


# celery的相關參數設定
class Config:
    broker_url = 'amqp://celeryman:pass1234@localhost:5672/celery_vhost'
    result_backend = 'redis://localhost:6379/'
    timezone = 'Asia/Taipei'


app.config_from_object(Config)  # 載入設定


# 在實例中加入task
@app.task(name='hello')
def hello(name='world'):
    return f'hello {name}'


@app.task(name='add')
def add(x, y):
    return x + y


# add periodic task
@app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):

    sender.add_periodic_task(5.0,
                             hello.s('there'),
                             name='every 5s hello')

    sender.add_periodic_task(5.0,
                             add.s(5, 5),
                             name='every 5s add')


if __name__ == '__main__':
    app.start()
