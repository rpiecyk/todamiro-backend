from kafka import KafkaProducer, KafkaAdminClient, KafkaConsumer
from kafka.admin import NewTopic

# Kafka configuration
BOOTSTRAP_SERVERS = 'localhost:29092'


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

        for message in self.kc:
            socketio.emit('new_message', {'topic_name': topic_name, 'message': message.value.decode('utf-8')},
                          broadcast=True)