Celery notes base on celery 4.1

# Celery component

1. Celery Beat: 工作排程，Beat 處理程序會讀取設定檔內容，週期性的將設定好要執行的 task 送到 work queue 中
2. Celery Worker: 執行工作的 consumer，通常會開啟多的 worker 來執行工作
3. Broker: 消息代理，就是儲存 task 的 work queue，通常選用 RabbitMQ(支持度最高) 或 redis
4. Producer: 產生 task 並且呼叫 Celery 的 api、function、decorator 把 task 送到 work queue
5. Result Backend: 儲存處理完的工作狀態、資訊或結果

```
 _______________
| Producer:     |          _________________                     ______________
|  -直接發佈task | ------> | 消息代理(Broker) | ---> (Worker) --->|Result Backend|
| Celery Beat:  | ------> |  Work Queue     | ---> (Worker) --->|儲存結果(資料庫)|
|  -排程發佈task |          -----------------                     --------------
 ---------------
```

# Basic setup
1. python version: 3.6
2. docker

[Install Celery](http://docs.celeryproject.org/en/master/getting-started/introduction.html#installation)
```bash
pip install -U Celery

# Bundles
pip install "celery[librabbitmq]"

pip install "celery[librabbitmq,redis,auth,msgpack]"
# python3 裝 librabbitmq 會失敗，https://github.com/celery/librabbitmq/issues/100
# 故 requirements 內改裝 amqp
pip install -r requirements.txt  # install celery
```

launch docker services
```bash
docker-compose up -d  # run broker(rabbitmq), backend(redis) and web-monitor(flower)
```
ps. celery 官方網站有提供不同 broker 與 backend 選擇的文件可以參考，本教學選擇 rabbitmq 與 redis 為官網最推薦的選擇。

# Run celery worker

一般 celery project 的基本結構如 basic_setup/， 

celery.py 定義 Celery 的實例，celeryconfig.py 定義各種參數設定，

最後是tasks.py，定義要執行的工作內容，但是事實上也可以根據需求合併一些檔案的配置。
```
basic_setup
   ├── __init__.py
   ├── celery.py
   ├── celeryconfig.py
   └── tasks.py
```

以下教學為求方便都把配置寫在單一檔案，如 vege.py，接下來要啟動 worker:

```bash
celery -A vege worker -l info  # launch worker
```
[celery command](http://docs.celeryproject.org/en/v4.1.0/reference/celery.bin.celery.html)

ps. -A proj or --app=proj 需要指到 Celery app 的 instance (module.path:attribute), 但他支援一些預設的搜尋規則,

以 -A proj 為例:
1. an attribute named proj.app
2. an attribute named proj.celery
3. any attribute in the module proj where the value is a Celery application, or
If none of these are found it’ll try a submodule named proj.celery
4. an attribute named proj.celery.app
5. an attribute named proj.celery.celery
6. Any attribute in the module proj.celery where the value is a Celery application

that is, proj:app for a single contained module, and proj.celery:app for larger projects.

啟動 worker 後會再終端看到配置的訊息(以下敘述相關配置):
```
 -------------- celery@Chrisde-MBP v4.1.0 (latentcall)
---- **** ----- 
--- * ***  * -- Darwin-16.7.0-x86_64-i386-64bit 2018-02-26 11:56:43
-- * - **** --- 
- ** ---------- [config]
- ** ---------- .> app:         hello:0x103188400
- ** ---------- .> transport:   amqp://celeryman:**@localhost:5672/celery_vhost
- ** ---------- .> results:     redis://localhost:6379/
- *** --- * --- .> concurrency: 4 (prefork)
-- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
--- ***** ----- 
 -------------- [queues]
                .> celery           exchange=celery(direct) key=celery
                
                [tasks]
                    . vege.hello
```
* app: 定義的 app 名稱
* transport or broker: broker url
* results: results url
* concurrency: is the number of prefork worker process used to process your tasks concurrently, 
The default concurrency number is the number of CPU’s on that machine (including cores)
* events: is an option that when enabled causes Celery to send monitoring messages (events) 
for actions occurring in the worker.
* queue: is the list of queues that the worker will consume tasks from
* tasks: 這個 app 配置了哪些 tasks (有時專案大的時候 tasks.py 散落個資料夾需注意 tasks 有沒有被加到 app 內)

ps. control + c shutdown worker

## run worker in the background

```bash
# launch worker name "w1"
celery multi start w1 -A vege -l info
# restart w1
celery multi restart w1 -A vege -l info 
# The stop command is asynchronous so it won’t wait for the worker to shutdown.
celery multi stop w1 -A vage -l info 
# use the stopwait command instead, this ensures all currently executing tasks are completed before exiting
celery multi stopwait w1 -A vage -l info 
```

celery multi doesn’t store information about workers 
so you need to use the same command-line arguments when restarting. 
Only the same pidfile and logfile arguments must be used when stopping.

預設的 .pid 和 .log 檔會放在當前目錄, 但是每個worker都會有, 為了防止衝突建議放到個別的資料夾, 
且命名不要重複。
```bash
mkdir -p /var/run/celery
mkdir -p /var/log/celery
celery multi start w1 -A proj -l info --pidfile=/var/run/celery/%n.pid \
                                      --logfile=/var/log/celery/%n%I.log
```

start multiple workers:
ex.
```bash
celery multi start 10 -A proj -l info -Q:1-3 images,video -Q:4,5 data \
    -Q default -L:4,5 debug
```

[celery multi command](http://docs.celeryproject.org/en/master/reference/celery.bin.multi.html#module-celery.bin.multi)


# Calling tasks and Keeping Results

```bash
celery shell  # into celery shell
```

## run task hello
you can call a task using the delay() or apply_async() method

```
>>>from vege import hello
>>>r = hello.delay('Chris')
>>>r
<AsyncResult: 459b476a-4f3a-4321-b4e6-e2c785a75deb>
>>>r.result
'hello Chris'
>>>r.status
'SUCCESS'
>>>r.id
'495c7826-c871-440a-a2e2-9cedbbb0b4c8'
>>>r.successful()
True
>>>r.backend  # 查看配置的 result backend
<celery.backends.redis.RedisBackend object at 0x10d33eb00>
```
apply_async() 支援較多的數的帶入例如運行時間(countdown)或發送的隊列(queue),

啟動worker時可以添加 -Q queue1,queue2,... 來設置此worker consume的 queue,

預設的queue是 celery, 也可以利用 task_routes 參數來指定 task對應的queue
```
>>>r2 = hello.apply_async(('Mark',), countdown=2, queue='celery')  #參數必須要可以迭代

>>> r2.ready()  # 可以查看 task 是否完成
True
>>>r2.get(timeout=1)  # 如果有配置result backend，可以查看return的值
'hello Mark'
```

The delay and apply_async methods return an AsyncResult instance, 
that can be used to keep track of the tasks execution state. 
But for this you need to enable a result backend so that the state can be stored somewhere.

## task status
PENDING -> STARTED -> SUCCESS

if "task_track_started" setting is enabled, 
or if the @task(track_started=True) option is set for the task.

PENDING -> STARTED -> RETRY -> STARTED -> RETRY -> STARTED -> SUCCESS

# Configuration

[celery config 配置](http://docs.celeryproject.org/en/master/userguide/configuration.html#configuration)

celery 可以非常簡單的添加一些設定，來完成許多不同的功能，

可以嘗試的在 celery shell 中 from vege import app，並且看看 app.conf 設定了哪些參數，

在利用 app.conf.xxx = 'value' 把值指定到 xxx 參數上，

或者是可以利用 app.conf.update(xxx1 = 'value1', xxx2 = 'value2') 的方式添加多種設定參數，

又或者是再啟動 worker 時，可以利用 celery control 的指令來添加不同設定，

當然正常而言需要的參數配置都應該事先寫在參數配置裡面，可以試著打開 vege.py 看看裡面的 Config 定義了些什麼。

恩...沒錯，只有定義了最最最基本的 broker 地址與 result_backend 地址，

基本上啟動 celery 唯一不能沒有的參數就是 broker_url，其他參數都可以視情況添加。

# Monitoring and Management

celery 提供了可以監視即管理 tasks 在 queue 裡面狀態的功能，

## Management Command-line Utilities 

透過指令來管理 celery，主要分為 control 與 inspect:

可以透過 celery control --help， celery inspect --help 查看用法

[celery 管理指令](http://docs.celeryproject.org/en/master/userguide/monitoring.html#management-command-line-utilities-inspect-control)

以下實作幾種不同用法
```bash
# 先啟動 worker
celery worker -A vege -l info
# 開啟新的終端並且輸入以下指令看看會產生什麼結果
celery -A vege control enable_events
celery -A vege inspect stats
```

## Flower: Real-time Celery web-monitor

在教學的一開始啟動 docker services 時，其實已經啟動了 flower，

可以現在前往 [localhost:5555](http://127.0.0.1:5555/)

帳號: celeryman  密碼: pass1234

就可以看到目前本機所啟動的 celery 資訊

如果想要裝在本地只需要在本地安裝 flower 並且啟動他

```bash
pip install flower  # 安裝 flower
celery -A proj flower  # 啟動 
celery -A proj flower --port=5555  # 可以指定別的 port，預設是5555
celery flower --broker=amqp://guest:guest@localhost:5672//  # 甚至可以指定 broker 的地址
```

## celery events: Curses Monitor

最後是 celery events 提供了一個簡單的介面，來記錄 tasks 得執行狀態。

```bash
celery -A vege events 
```

一般來說 flower 提供的管理監控功能是比較方便的，建議大家可以使用 flower！

當然 celery 是把 tasks 送到 broker 上，如果對這些 broker 本身的原生操作熟的話，

也可以利用 broker 本身的指令，來監控這些 tasks。

# Periodic Tasks

celery beat 排程執行 task 會將 task 執行時間記錄在"celerybeat-schedule", 作為下一次排程的依據，

而這個 scheduler 所使用的時間依據，預設為 UTC time zone，可以在 config 設定 timezone 來更改時區，

讓 task 排程工作在 celery 裡面有兩種做法，一種是直接在 celery config 設定 beat_schedule，

而另一種是在腳本中使用 add_periodic_task() 的方法，來設定 beat_schedule！

以下進行兩種實作：

## 直接設定 beat_schedule，要記得 celery beat 是需要啟動的！
```bash
# launch celery beat
celery -A vege1 beat -l info 
# 另一個終端開啟 worker
celery -A vege1 worker -l info
```
觀察一下 vege1.py 的 beat_schedule 設定有幾個重點！

以每 10 秒發送的 task 為例，'add-every-10-seconds' 為 task 名稱，

schedule 對應到的為秒數或 timedelta 物件，

args 則是 task 的 *args，但 args 對應的 value 必須要是可以迭代的，

比如說 ['friend'] 或是 ('friend',)，否則會報錯。

再來就是 add-every-minute 這個 task 使用了一個叫 crontab 的方法，

簡單得來說 crontab 就是設定特定的時間來發出 task 而不是間隔幾秒就發！

[crontab 用法](http://docs.celeryproject.org/en/master/reference/celery.schedules.html#celery.schedules.crontab)

另外 celery scheduler 也提供了 [solar](http://docs.celeryproject.org/en/master/reference/celery.schedules.html#celery.schedules.solar) 物件來當排程的參考。 

## 再來是設定 add_periodic_task() 的實作！
```bash
# -B 可以直接啟動 celery beat
# -Q 定義啟動後要開啟的 queue 名稱(可以一次開啟多個)
# -s 可以定義記錄排成時間的 beat-schedule 文件的名稱以及位置(預設為 celerybeat-schedule.db)
celery -A vege2 worker -l info -Q queue1,queue2 -B -s beat-record
```
[celery beat command](http://docs.celeryproject.org/en/v4.1.0/reference/celery.bin.beat.html)

在 vege2.py 中，基本配置一樣，只是改變了設定排程的方式，

首先在第 30 行有 @app.on_after_configure.connect，的用意在 celery 官方說明為:

Setting these up from within the on_after_configure handler means that we’ll not evaluate the app at module level when using hello.s().

這是 celery [Signal](http://docs.celeryproject.org/en/master/userguide/signals.html) 的設定，有四種設定:

* on_configure: Signal sent when app is loading configuration.

* on_after_configure: Signal sent after app has prepared the configuration.

* on_after_finalize: Signal sent after app has been finalized.

* on_after_fork: Signal sent by every new process after fork.

而值得一提的，add_periodic_task()方法中，第二個 args 必須要填入，signatures 的方法，

就是 hello.s() 與 add.s()，會在[進階用法](https://github.com/htkuan/Celery_notes/blob/master/advance.md)中說明，

最後給定 queue 的名稱，可以把不同的 task 分流到不同的 queue 裡面。
