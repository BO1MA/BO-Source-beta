import redis
from datetime import datetime

# Initialize Redis connection
redis_client = redis.StrictRedis(
    host=os.getenv("REDIS_HOST", "127.0.0.1"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    password=os.getenv("REDIS_PASSWORD", None),
    decode_responses=True
)

def log_transaction(user_id, transaction_type, amount, category="default"):
    """Logs a transaction for a user."""
    transaction_id = redis_client.incr("transaction_id")
    transaction_data = {
        "user_id": user_id,
        "type": transaction_type,
        "amount": amount,
        "category": category,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    redis_client.hset(f"transaction:{transaction_id}", mapping=transaction_data)
    redis_client.rpush(f"user:{user_id}:transactions", transaction_id)

def get_transaction_history(user_id):
    """Retrieves the transaction history for a user."""
    transaction_ids = redis_client.lrange(f"user:{user_id}:transactions", 0, -1)
    history = []
    for transaction_id in transaction_ids:
        history.append(redis_client.hgetall(f"transaction:{transaction_id}"))
    return history