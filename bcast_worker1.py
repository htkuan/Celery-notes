from __future__ import absolute_import
from celery import Celery
from kombu.common import Broadcast

app = Celery('bcast_w1')  # 建立一個Celery的instance


# celery的相關參數設定
class Config:
    broker_url = 'amqp://celeryman:pass1234@localhost:5672/celery_vhost'
    result_backend = 'redis://localhost:6379/'


app.config_from_object(Config)  # 載入設定

app.conf.task_queues = (Broadcast('bcast_q', 'bcast_w1'),)


# 在實例中加入task
@app.task(name='bcast')
def hello(msg='default'):
    return msg


if __name__ == '__main__':
    app.start()
