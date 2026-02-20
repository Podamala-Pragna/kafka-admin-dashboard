# Node 4 config
KAFKA_BROKER = "10.147.19.122:9092"   # broker node's ZT IP
ADMIN_HOST   = "10.147.19.157"      # your ZT IP from step 1
ADMIN_PORT   = 5001                      # use 5001 to avoid conflicts

ADMIN_BASE   = f"http://{ADMIN_HOST}:{ADMIN_PORT}"
TOPICS_ENDPOINT = f"{ADMIN_BASE}/topics"

SQLITE_DB = "project2.db"

