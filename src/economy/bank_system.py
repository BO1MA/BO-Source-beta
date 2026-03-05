import os  # Ensure the 'os' module is imported for environment variable access
import redis
import datetime
import random
from datetime import timedelta

# Initialize Redis connection
redis_client = redis.StrictRedis(
    host=os.getenv("REDIS_HOST", "127.0.0.1"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    db=int(os.getenv("REDIS_DB", 0)),
    password=os.getenv("REDIS_PASSWORD", None),
    decode_responses=True
)

# Replace SQLite functions with Redis equivalents

def init_db():
    # No initialization needed for Redis
    pass

def has_bank_account(user_id):
    return redis_client.hexists(f"user:{user_id}", "has_account")

def open_bank_account(user_id, category="default"):
    if not has_bank_account(user_id):
        redis_client.hset(f"user:{user_id}", mapping={
            "bank_balance": 100,
            "has_account": True,
            "is_cheater": False,
            "is_banned": False,
            "last_daily": None,
            "category": category
        })
        return f"✅ تم فتح حساب بنكي بنجاح في الفئة '{category}'! رصيدك الابتدائي هو 100 نقطة."
    return "❌ لديك حساب بنكي بالفعل."

def get_balance(user_id):
    return int(redis_client.hget(f"user:{user_id}", "bank_balance") or 0)

def update_balance(user_id, amount):
    redis_client.hincrby(f"user:{user_id}", "bank_balance", amount)

def claim_daily(user_id):
    last_daily = redis_client.hget(f"user:{user_id}", "last_daily")
    if last_daily:
        last_daily = datetime.strptime(last_daily, "%Y-%m-%d %H:%M:%S")
        if datetime.now() - last_daily < timedelta(days=1):
            return "❌ لقد حصلت على هديتك اليومية بالفعل. حاول مرة أخرى غدًا."

    gift = random.randint(50, 200)
    redis_client.hset(f"user:{user_id}", "bank_balance", get_balance(user_id) + gift)
    redis_client.hset(f"user:{user_id}", "last_daily", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return f"💰 لقد حصلت على {gift} نقطة كهديتك اليومية!"

def transfer_points(from_user, to_user, amount, category="default"):
    if redis_client.hget(f"user:{from_user}", "category") != category or redis_client.hget(f"user:{to_user}", "category") != category:
        return "❌ لا يمكنك تحويل النقاط بين حسابات في فئات مختلفة."

    if get_balance(from_user) < amount:
        return "❌ رصيدك لا يكفي لإتمام عملية التحويل."

    update_balance(from_user, -amount)
    update_balance(to_user, amount)
    return f"✅ تم تحويل {amount} نقطة بنجاح من حسابك إلى حساب المستخدم الآخر في الفئة '{category}'."