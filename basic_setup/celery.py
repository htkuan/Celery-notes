from __future__ import absolute_import  # 拒絕隱式的引用(如果程式名稱跟celery一樣）
from celery import Celery


app = Celery('basic', include=['basic_setup.tasks'])

app.config_from_object('basic_setup.celeryconfig')


if __name__ == '__main__':
    app.start()
