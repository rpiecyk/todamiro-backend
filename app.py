from flask import Flask, render_template, request
from flask_cors import CORS
from flask_socketio import SocketIO, send, emit
from kvka import KafkaService
import logging
#import eventlet
#eventlet.monkey_patch()

FORMAT = '%(asctime)s %(message)s'
logging.basicConfig(format=FORMAT)
logging.getLogger().addHandler(logging.StreamHandler())
debug = True

app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'todamiro'
#socketio = SocketIO(app,async_mode = 'eventlet')
socketio = SocketIO(app, cors_allowed_origins="http://localhost:5173")

kafka_service = KafkaService()

@app.route('/')
def hello_world():
    return 'hello world'

def ack():
    print('message was received!')


@socketio.on('connect')
def test_connect(auth):
    logging.info('connected')
    emit('my response', {'data': 'Connected'})


@socketio.on('fetch_topics')
def handle_message(data):
    print('topics:')


# @socketio.on('feedback')
# def handle_message(mess):
#     send(mess)


@socketio.on('create_topic')
def handle_create_topic(data):
    topic_name = data['topic_name']
    created_topic = kafka_service.create_topic(topic_name)
    logging.info(created_topic)
    #emit('topic_created', {'topic_name': created_topic}, broadcast=True)


messages = {}
@socketio.on("send_message")
def handle_send_message(message):
    print('tu jestem')
    existing_messages = messages.get(message["id"], [])
    messages[message["id"]] = existing_messages + [message]
    emit("recieve_messages", messages[message["id"]], broadcast=True)
    topic_name = "five_topic"
    message = f"{message['email']}$${message['message']}"
    response = kafka_service.push_message(topic_name, message)
    print(response)


@socketio.on("get_messages")
def handle_get_messages(data):
    print('tam jestem')
    id = data["id"]
    emit("recieve_messages", messages.get(id, []), broadcast=True)


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
    socketio.run(app, debug=debug, port=5001)
