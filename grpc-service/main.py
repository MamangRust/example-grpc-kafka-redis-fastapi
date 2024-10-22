import grpc
from concurrent import futures
from proto import task_pb2_grpc, task_pb2  # Use absolute import
import sqlite_db
import kafka_service
import redis_cache
import asyncio
import uuid
from jose import jwt
from grpc import StatusCode
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

class TaskService(task_pb2_grpc.TaskServiceServicer):
    
    # Middleware for JWT validation
    def validate_jwt(self, context):
        metadata = dict(context.invocation_metadata())
        token = metadata.get('authorization')
        if not token or not token.startswith('Bearer '):
            logger.warning("Missing or invalid token")
            context.abort(StatusCode.UNAUTHENTICATED, "Missing or invalid token")
        
        try:
            jwt_token = token.split(' ')[1]
            payload = jwt.decode(jwt_token, SECRET_KEY, algorithms=[ALGORITHM])
            logger.info("Token validated for user: %s", payload['sub'])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            logger.error("Token expired")
            context.abort(StatusCode.UNAUTHENTICATED, "Token expired")
        except jwt.InvalidTokenError:
            logger.error("Invalid token")
            context.abort(StatusCode.UNAUTHENTICATED, "Invalid token")

    async def AddTask(self, request, context):
        # Validate JWT
        user_id = self.validate_jwt(context)
        
        task_id = str(uuid.uuid4())
        task_data = {"id": task_id, "title": request.title, "description": request.description}
        
        # Save task to Kafka
        await kafka_service.produce_task(task_data)
        logger.info("Task produced to Kafka: %s", task_data)
        
        # Save task to SQLite
        sqlite_db.save_task_to_db(task_id, request.title, request.description)
        logger.info("Task saved to SQLite: %s", task_data)
        
        # Cache task to Redis (optional)
        redis_cache.cache_task(task_data)
        logger.info("Task cached in Redis: %s", task_data)
        
        return task_pb2.TaskResponse(message="Task added successfully")

    async def GetTask(self, request, context):
    # Validate JWT
        user_id = self.validate_jwt(context)

        logger.info("Fetching task with ID: %s", request.id)
        
        # Try getting task from Redis cache
        cached_task = await redis_cache.get_cached_task(request.id)  # Make sure to await this
        if cached_task:
            logger.info("Task retrieved from Redis: %s", cached_task)
            return task_pb2.Task(id=cached_task['id'], title=cached_task['title'], description=cached_task['description'])
        
        # If not found in Redis, retrieve from SQLite
        task = sqlite_db.get_task_from_db(request.id)
        if not task:
            logger.warning("Task not found with ID: %s", request.id)
            context.abort(grpc.StatusCode.NOT_FOUND, "Task not found")
        
        # Cache task to Redis
        redis_cache.cache_task({"id": task[0], "title": task[1], "description": task[2]})
        logger.info("Task cached in Redis: %s", task)

        return task_pb2.Task(id=task[0], title=task[1], description=task[2])

    async def GetAllTasks(self, request, context):
        # Validate JWT
        user_id = self.validate_jwt(context)
        
        tasks = sqlite_db.get_all_tasks()
        task_list = task_pb2.TaskList()
        for task in tasks:
            task_list.tasks.add(id=task[0], title=task[1], description=task[2])
        logger.info("Fetched all tasks: %s", len(tasks))
        return task_list

async def serve():
    server = grpc.aio.server()

    sqlite_db.init_db()

    task_pb2_grpc.add_TaskServiceServicer_to_server(TaskService(), server)
    server.add_insecure_port('[::]:50051')
    await server.start()
    logger.info("Server started on port 50051")
    await server.wait_for_termination()

if __name__ == "__main__":
    asyncio.run(serve())
