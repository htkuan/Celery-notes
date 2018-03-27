FROM python:3.6.4-alpine

RUN pip install flower redis
RUN pip install celery==4.1.0
# celery 4.2
#RUN pip install https://github.com/celery/celery/archive/master.zip

ADD config.py /opt/config.py
CMD flower --broker=$BROKER_URL --conf=/opt/config.py