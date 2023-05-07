import redis

from ionos import settings

redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
