from confluent_kafka import Producer, KafkaException
from api.logger import logger
from api.settings import settings
import sys

class KafkaProducer:
    def __init__(self):
        self._producer = Producer(
            {"bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS}
        )
        print("Kafka producer initialized with bootstrap servers: {}".format(settings.KAFKA_BOOTSTRAP_SERVERS))

    def delivery_report(self, err, msg):
        """Called once for each message produced to indicate delivery result.
        Triggered by poll() or flush()."""
        if err is not None:
            print("Message delivery failed: {}".format(err))
            logger.warning("Message delivery failed: {}".format(err))
        else:
            print("Message delivered to {} [{}]".format(msg.topic(), msg.partition()))
            logger.info("Message delivered to {} [{}]".format(msg.topic(), msg.partition()))

    def poll(self):
        print("Polling Kafka producer...")
        self._producer.poll(1)

    def produce(self, topic, value, on_delivery=None):
        print(f"Producing message to topic '{topic}': {value}")
        try:
            self._producer.produce(topic, value, on_delivery=on_delivery or self.delivery_report)
            print("Message production scheduled successfully")
        except BufferError:
            print("%% Local producer queue is full (%d messages pending delivery)" % len(self._producer))
            # Wait for messages to be delivered
            self._producer.poll(1)
            # Try again
            self._producer.produce(topic, value, on_delivery=on_delivery or self.delivery_report)
        except KafkaException as e:
            print(f"Kafka error during production: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error during production: {e}")
            raise

    def flush(self):
        print("Flushing Kafka producer...")
        self._producer.flush()
        print("Kafka producer flush completed")

kafka_producer = KafkaProducer()