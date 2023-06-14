#import eventlet
#eventlet.monkey_patch()

from flask import Flask, render_template, request
from flask_cors import CORS
from flask_socketio import SocketIO, send, emit
#from kvka import KafkaService
from fire import Fire
import logging
import json
from threading import Thread


from kafka import KafkaProducer, KafkaAdminClient, KafkaConsumer
from kafka.admin import NewTopic

# Kafka configuration
#BOOTSTRAP_SERVERS = 'localhost:29092'
BOOTSTRAP_SERVERS = '10.0.101.20:29092'
WS_PORT = 3001


class KafkaService:
    def __init__(self):
        self.topics = set()
        self.ka = KafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVERS)
        self.kp = KafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)
        self.kc = KafkaConsumer(bootstrap_servers=BOOTSTRAP_SERVERS,
                         enable_auto_commit=False,
                         group_id='my-group')

    def create_topic(self, topic_name):
        new_topic = NewTopic(topic_name, num_partitions=1, replication_factor=1)
        self.ka.create_topics([new_topic])
        self.topics.add(topic_name)
        return topic_name

    def push_message(self, topic_name, message):
        #if topic_name not in self.topics:
        #    return "Topic doesn't exist."
        self.kp.send(topic_name, message.encode('utf-8'))
        self.kp.flush()
        return "Message sent successfully."

    def consume_messages(self, topic_name):
        self.kc.subscribe([topic_name])
        print('got here')
        for message in self.kc:
            v = message.value.decode('utf-8')
            print('__')
            print(topic_name)
            print(v)
            print('__')
            v_email, v_date, v_message = v.split('$$')
            payload = {'date':1686692469940, 'email': '@softserveinc.com', 'id': topic_name, 'message': v}
            #socketio.emit('receive_messages', {'topic_name': topic_name, 'message': [message.value.decode('utf-8')]})
            socketio.emit('receive_message', [payload])


class KafkaConsumerThread(Thread):
    def __init__(self, topic_name):
        super().__init__()
        self.topic_name = topic_name
        self.consumer = KafkaConsumer(bootstrap_servers=BOOTSTRAP_SERVERS,
                                      enable_auto_commit=False,
                                      group_id='my-group')

    def run(self):
        self.consumer.subscribe([self.topic_name])
        for message in self.consumer:
            v = message.value.decode('utf-8')
            payload = {'date':1686692469940, 'email': '@softserveinc.com', 'id': self.topic_name, 'message': v}
            print('im in run')
            print(payload)
            socketio.emit('receive_message', [payload])


FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(format=FORMAT)
logging.getLogger().addHandler(logging.StreamHandler())
debug = True

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'todamiro'
#socketio = SocketIO(app,async_mode = 'eventlet')
#socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173", logger=True, engineio_logger=True)
socketio = SocketIO(app, cors_allowed_origins="https://todamiro.com")
#socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173",async_mode = 'eventlet')

kafka_service = KafkaService()
fire_base = Fire()


@app.route('/')
def hello_world():
    return 'hello world'

def ack():
    print('message was received!')


@socketio.on('connect')
def test_connect(auth):
    print('connected')
    logging.info('connected')
    emit('my response', {'data': 'Connected'})


topics = {}
@socketio.on('get_topics')
def handle_message():
    tops = fire_base.fetch_topics()
    #print(tops)
    #tops = [{'slots': -4, 'date': '2023-06-13T15:01:00.312Z', 'topic': 'ogladac_slonia', 'id':1, 'slotsTaken':0,'place':'go'}]
    emit("receive_topics", tops, broadcast=True)


topics = {}
@socketio.on('get_topic')
def handle_message(data):
    print('asking for a topic')
    tid = data['id']
    tops = fire_base.fetch_topic(tid)
    print(topic_subscribers)
    tops['subscribed'] = int(data['email'] in topic_subscribers.get(tid,[]))
    print(tops)
    tops['slotsTaken'] = min(tops.get('slotsTaken',10000),tops['slots'])
    emit("receive_topic", tops, broadcast=True)


@socketio.on('topic_created')
def handle_create_topic(data):
    print('creating')
    data['slotsTaken'] = 0
    print(data)
    topic_name = data['id']
    topics[data['id']] = 0
    created_topic = kafka_service.create_topic(topic_name)
    fire_base.put_topic(topic_name,data)
    print(created_topic)
    logging.info(created_topic)
    emit('new_topic', data, broadcast=True)


messages = {}
@socketio.on("send_message")
def handle_send_message(message):
    existing_messages = messages.get(message["id"], [])
    messages[message["id"]] = existing_messages + [message]
    #print(messages[message["id"]])
    emit("receive_messages", {'id':message["id"],'messages':messages[message["id"]]}, broadcast=True)
    topic_name = message['id']
    #print('tn:', topic_name)
    message = f"{message['email']}$${message['date']}$${message['message']}"
    response = kafka_service.push_message(topic_name, message)
    print(response)


@socketio.on("get_messages")
def handle_get_messages(data):
    id = data["id"]
    #print(messages.get(id, []))
    emit("receive_messages", {'id':id,'messages':messages.get(id, [])}, broadcast=True)


@socketio.on('starting_consumer')
def handle_start_consumer(data):
    print(f"starting consumer for {data['id']}")
    #jdata = json.loads(data.replace("'",'"'))
    #topic_name = 'nieogladanie' #data['topic_name']
    topic_name = data['id']#'9095551e-b296-4663-bd44-1563e19badd0'
    try:
        a=1#Thread(target=kafka_service.consume_messages, args=(topic_name,)).start()
    except ValueError as ve:
        print(ve)
        logging.warning('executor already running')


@socketio.on('go_consumer')
def handle_start_consumer(data):
    jdata = json.loads(data.replace("'",'"'))
    topic_name = jdata['id']
    consumer_thread = KafkaConsumerThread(topic_name)
    consumer_thread.start()


topic_subscribers = {}
@socketio.on('subscribe')
def handle_add_subscriber(data):
    tid = data['id']
    print('adding')

    subscribers = topic_subscribers.get(data['id'],[])
    subscribers.append(data['email'])
    topic_subscribers[data['id']] = subscribers

    adding = fire_base.mod_subscriber(tid,1)
    print(adding)
    emit('subscribed', data, broadcast=True)


@socketio.on('unsubscribe')
def handle_remove_subscriber(data):
    print('unsubscribing')
    tid = data['id']
    usr = data['email']
    subs = topic_subscribers.get(tid)
    if subs and usr in subs:
        new_subs = subs.remove(usr)
        topic_subscribers[tid] = new_subs or []
    removing = fire_base.mod_subscriber(tid,-1)
    print(removing)
    a=1
    print(topic_subscribers)
    emit('unsubscribed', data) 


# @socketio.on('kafkaconsumer') ewfwe
# def kafkaconsumer(message):
#     consumer = KafkaConsumer(group_id='consumer-1',
#                              bootstrap_servers=BOOTSTRAP_SERVERS)
#     tp = TopicPartition(TOPIC_NAME, 0)
#     print('ha1')
#     # register to the topic
#     consumer.assign([tp])

#     # obtain the last offset value
#     consumer.seek_to_end(tp)
#     lastOffset = consumer.position(tp)
#     consumer.seek_to_beginning(tp)
#     emit('kafkaconsumer1', {'data': ''})
#     print('ha2')
#     for message in consumer:
#         msg = [{'message': message.value.decode('utf-8'), 'email': 'mhaic@softserveinc.com', 'date': 1686674336650, 'id': '9095551e-b296-4663-bd44-1563e19badd0'}]
#         print(msg)
#         print('emitting')
#         emit('receive_messages', msg, broadcast=True)
#         #print(message)
#         if message.offset == lastOffset - 1:
#             break
#     print('ha3')
#     consumer.close()


# @socketio.on('send_message')
# def handle_push_message(data):
#     #topic_name = data['topic_name']
#     topic_name = "five_topic"
#     #message = f"{data['email']}$${data['message']}"
#     #response = kafka_service.push_message(topic_name, message)
#     #logging.info('message_sent', response)
#     print(data)
#     send(data)
#     emit('recieve_messages', {'response': response}, broadcast=True)


if __name__ == '__main__':
    #socketio.init_app(app, cors_allowed_origins="*")
    #socketio.init_app(app, cors_allowed_origins=['http://localhost:5173'])
    logging.info('starting now')
    socketio.run(app, debug=debug, host='0.0.0.0', port=WS_PORT, allow_unsafe_werkzeug=True)
