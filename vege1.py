from __future__ import absolute_import
from celery import Celery
from celery.schedules import crontab
from celery import chain

app = Celery('beat1')  # 建立一個Celery的instance


# celery的相關參數設定
class Config:
    broker_url = 'amqp://celeryman:pass1234@localhost:5672/celery_vhost'
    # result_backend = 'redis://localhost:6379/2'
    result_backend = 'rpc://'
    task_ignore_result = True
    # task_store_errors_even_if_ignored = True
    timezone = 'Asia/Taipei'
    beat_schedule = {
        # 每 10 秒發送這個 hello 這個 task
        'add-every-10-seconds': {
            'task': 'vege1.hello',
            'schedule': 100.0,
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


@app.task(task_store_errors_even_if_ignored=True)
def add(x, y):
    ans = x + y
    if ans % 2:
        return ans
    else:
        raise Exception


@app.task
def test(x):
    out = 'start:'
    out += x
    print(out)
    return out


@app.task
def run_chain(num):
    chain(add.s(2, num), add.s(7), add.s(10)).apply_async()


if __name__ == '__main__':
    app.start()
