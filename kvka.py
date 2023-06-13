from kafka import KafkaProducer, KafkaAdminClient
from kafka.admin import NewTopic

# Kafka configuration
BOOTSTRAP_SERVERS = 'localhost:29092'


class KafkaService:
    def __init__(self):
        self.topics = set()
        self.ka = KafkaAdminClient(bootstrap_servers=BOOTSTRAP_SERVERS)
        self.kp = KafkaProducer(bootstrap_servers=BOOTSTRAP_SERVERS)

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
