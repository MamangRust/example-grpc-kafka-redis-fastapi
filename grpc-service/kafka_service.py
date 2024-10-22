from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import asyncio
import json

KAFKA_TOPIC = 'tasks'

async def produce_task(task_data):
    producer = AIOKafkaProducer(bootstrap_servers='kafka:9092')
    await producer.start()
    try:
        # Serialize task_data to JSON
        await producer.send_and_wait(KAFKA_TOPIC, json.dumps(task_data).encode('utf-8'))
    finally:
        await producer.stop()

async def consume_tasks():
    consumer = AIOKafkaConsumer(KAFKA_TOPIC, bootstrap_servers='kafka:9092', group_id="task_group")
    await consumer.start()
    try:
        async for msg in consumer:
            task_data = json.loads(msg.value.decode('utf-8'))
            print(f"Received task: {task_data}")
    finally:
        await consumer.stop()

# To run the consumer
if __name__ == '__main__':
    asyncio.run(consume_tasks())
