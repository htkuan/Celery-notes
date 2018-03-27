# Routing Tasks

在基本教學中有提到可以開啟多個 worker 並且讓 worker 執行不同 queue 裡的 tasks，

在 celery 從 worker 的數量與命名(甚至是hostname)，跟 worker 對應的 queue 都可以利用啟動指令，

或者是 config 參數配置達成，更支援了 AMQP 協定的 broker 路由設定(有實現 AMQP 的 broker 限定 ex. rabbitmq)。

在 vege3.py 中配置了 task_routes ，可以指定不同的 tasks 推送到哪個 queue
```bash
# 啟動一個 worker -D 表示背景執行
# 開啟兩個 queue 叫 queue1 queue2
# 並且規定 pid 檔的產生路徑為空(就是不要有這個檔案拉)
celery -A vege3 worker -D -l info -Q queue1,queue2 --pidfile=
# 查看 worker 狀態
celery status -A vege3
# stop worker if you need
pkill -9 -f 'celery worker'
```
啟動後，可以進入 celery shell 發送 tasks 並且到 flower 上觀看 tasks 被發到哪個 queue 內。

而另外使用 RabbitMQ 為 broker 的話可以定義 Queue 的優先級來實現 [priority queue](http://docs.celeryproject.org/en/master/userguide/routing.html#special-routing-options)

如果要更彈性的選擇 celery 也針對實現 AMQP 協議的 broker 提供專用的 routing 定義

[Celery AMQP usage](http://docs.celeryproject.org/en/master/userguide/routing.html#amqp-primer)

# Designing Work-flows

sometimes you may want to pass the signature of a task invocation to another process 
or as an argument to another function, for this Celery uses something called "signatures".

```bash
celery -A vege4 worker -l info -B
```

## signatures
A signature wraps the arguments and execution options of a single task 
invocation in a way such that it can be passed to functions or even serialized and sent across the wire.
用法類似 functools.partial 的感覺

```
>>> hello.signature(('haha',), countdown=5)
vege.hello('haha')
>>> hello.s('haha')  # shortcut
vege.hello('haha')

>>> s1 = hello.s('haha')
>>> res = s1.delay()
>>> res.get()
'hello haha'
```
ps. 如果 signatures 的參數不齊全, 會啟用partial機制, 就必須在調用 delay() 或 apply_async() 時把參數補足

ps. (group, map, chain, chord, starmap, chunks) are signature objects themselves, 
so they can be combined in any number of ways to compose complex work-flows.

## Groups
A group calls a list of tasks in parallel, 
and it returns a special result instance that lets you inspect the results as a group, 
and retrieve the return values in order.

```
>>> from celery import group
>>> from vege import add

>>> group(add.s(i, i) for i in range(10))().get()
[0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

# Partial group
>>> g = group(add.s(i) for i in range(10))
>>> g(10).get()
[10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
```

## Chains
Tasks can be linked together so that after one task returns the other is called:

```
>>> from celery import chain
>>> from vege import add

>>> chain(add.s('chris', 'kuan') | hello.s())().get()
'hello chriskuan'
# or
>>> (add.s('chris', 'kuan') | hello.s())().get()
'hello chriskuan'

>>> g = chain(add.s('kuan') | hello.s())
>>> g('chris').get()
'hello chriskuan'
```

## Chords
A chord is a group with a callback

[More Designing Work-flows](http://docs.celeryproject.org/en/master/userguide/canvas.html)

# Remote Control

[Monitoring](http://docs.celeryproject.org/en/master/userguide/monitoring.html#guide-monitoring)

```bash
celery -A proj inspect active

celery -A proj inspect active --destination=celery@example.com

celery -A proj inspect --help

celery -A proj control --help

celery -A proj control enable_events

celery -A proj events --dump

celery -A proj events

celery -A proj control disable_events

celery -A proj status
```

# Celery 的最佳用法

整理至 celery 官方與 "寫python web買一個未來" 一書

1. 使用自動擴充：
多處理程序與Gevent 模式的worker支援自動擴充，透過 --autoscale 參數實現
$ celery -A proj worker -l info --autoscale=6,3
 --autoscale 接受兩個數，根據上方“--autoscale=6,3”， 代表處理程序池平時保持3個處理程序，最大平行處理程序可以到達6個


2. 善用遠端debug：
(debuging)[http://docs.celeryproject.org/en/master/userguide/debugging.html?highlight=pdb]
Celery 支援遠端使用 pdb 偵錯！
```python
from celery import task
from celery.contrib import rdb

@task()
def add(x, y):
    result = x + y
    rdb.set_trace()  # <- set break-point
    return result
```
在終端發布 add(1,2)
```
[INFO/MainProcess] Received task:
    tasks.add[d7261c71-4962-47e5-b342-2448bedd20e8]
[WARNING/PoolWorker-1] Remote Debugger:6900:
    Please telnet 127.0.0.1 6900.  Type `exit` in session to continue.
[2011-01-18 14:25:44,119: WARNING/PoolWorker-1] Remote Debugger:6900:
    Waiting for client...
```
可以到 127.0.0.1:6900 偵錯


3. 合理安排工作週期：
專案中會有許多排程工作，排成時間需注意幾點
＊ 根據工作特性，盡量把工作打散，不要擠在同一個時間(尤其是整點)
＊ 對於需要寫入檔案系統或是資料庫的工作，盡可能的把工作選在存取的低峰期
＊ 不要緊的工作排到系統負載較低時發送


4. 合理使用Queue和優先順序：
不要把工作都放在預設的Queue，要根據工作形質來分Queue，合理安排工作的優先順序，讓應該及時完成的工作擁有比較高的優先順序，讓這些工作不會因阻塞而影響使用者體驗。
再來是合理使用 apply_async 方法臨時性的切換徂列與優先順序。


5. 保障業務邏輯的交易性：
Celery雖然提供錯誤重試的機制，但是沒有提供工作的交易性，所以如果一部份工作執行成功一部份失敗，成功的部分是沒有提供回覆方法的，所以一開始設計工作排程的時候需要對此考慮，且要對重試機制有明確的了解。


6. 關閉你不想要的功能：
比如說對執行的結果沒有興趣可以關閉它
```python
@app.task(ignore_result=True)
def task(...):
    ...
```
或是專案不需要限速，可以把 ‘worker_disable_rate_limits=true’


7. 使用閱後即焚模式：
使用Queue得時候，預設是使用持久化得方式來確保工作執行，如果工作不需要，可以使用閱後即焚(transient)模式：
```python
from kombu import Queue
Queue(‘transient’, routing_key=’transient’, delivery_mode=1)
```


8. 善用Prefetch模式：
worker 處理程序預設每次從borker取得 worker_prefetch_multiplier 的工作數，如果工作都比較細小，可以修改此值，讓每次取得更多的工作數


9. 善用工作流：
如果工作有呼叫鍊，下一步工作需要等待上一部工作的結果，就不應該使用同步子工作，以一個爬取電商網站為例，假設需要四部工作
1.取得抓取畫面
2.抓取對應頁面
3.解析頁面資料
4.把需要的資料存到資料庫
所以就不能把工作寫成
```python
@app.task
def page_crawler():
    url = get_url.delay().get()
    page = fetch_page.delay().get()
    info = parse_page.delay().get()
    store_page().delay(info)
@app.task
def get_url():

@app.task
def fetch_page():

@app.task
def parse_page():

@app.task
def store_page():

```
應該寫成
```python
def page_crawler():
    chain = get_url.s() | fetch_page.s() | parse_page.s() | store_page.s()
    chain()
```


