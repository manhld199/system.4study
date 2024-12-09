
BOOSTRAP_SERVER = 'kafka:29092'

def get_enrolled_courses(days=None):
  from datetime import datetime, timedelta, timezone
  from pymongo import MongoClient

  try:
    # Replace with your MongoDB Atlas connection string
    connection_string = "mongodb+srv://admin:admin@is353.nvhsc.mongodb.net/4study?retryWrites=true&w=majority&appName=is353"
    client = MongoClient(connection_string)

    # Access the database and collection
    db = client["4study"]
    user_collection = db["users"]

    # Calculate the start date if `days` is provided
    now = datetime.now(timezone.utc)  # Current UTC datetime with timezone info
    start_date = now - timedelta(days=days) if days else None

    # Aggregation pipeline
    pipeline = [
      {"$unwind": "$list_courses"},
      {
        "$match": {
          "list_courses.enroll_time": {
            "$lte": now,  # Use timezone-aware datetime
            **({"$gte": start_date} if start_date else {})
          }
        }
      },
      {"$sort": {"list_courses.enroll_time": -1}},
      {
        "$group": {
          "_id": "$_id",
          "list_courses": {
            "$push": {
              "course_id": "$list_courses.course_id",
              "enroll_time": "$list_courses.enroll_time"
            }
          }
        }
      },
      {
        "$project": {
          "_id": 0,
          "user_id": "$_id",
          "list_courses": 1
        }
      }
    ]

    # Execute the aggregation pipeline
    results = list(user_collection.aggregate(pipeline))
    return results

  except Exception as e:
    print("An error occurred:", e)
    return []

def create_topic_if_not_exists(topic_name, num_partitions=1, replication_factor=1):
  from kafka.admin import KafkaAdminClient, NewTopic
  
  admin_client = None  # Khởi tạo admin_client là None
  
  try:
    # Khởi tạo Kafka Admin Client
    admin_client = KafkaAdminClient(
      bootstrap_servers=BOOSTRAP_SERVER,  # Sử dụng hostname của container Kafka
      client_id="kafka_admin"
    )

    # Lấy danh sách các topic đã tồn tại
    existing_topics = admin_client.list_topics()

    if topic_name not in existing_topics:
      print(f"Topic '{topic_name}' does not exist. Creating...")
      # Tạo topic mới
      topic = NewTopic(
        name=topic_name,
        num_partitions=num_partitions,
        replication_factor=replication_factor
      )
      admin_client.create_topics(new_topics=[topic], validate_only=False)
      print(f"Topic '{topic_name}' created successfully!")
    else:
      print(f"Topic '{topic_name}' already exists.")

    admin_client.close()
  except Exception as e:
    print(f"Error creating topic: {e}")

def custom_serializer(obj):
  from datetime import datetime
  from bson import ObjectId

  if isinstance(obj, ObjectId):
    return str(obj)  # Chuyển ObjectId thành chuỗi
  elif isinstance(obj, datetime):
    return obj.isoformat()  # Chuyển datetime thành chuỗi ISO 8601
  raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def prepare_data(data):
  from datetime import datetime
  from bson import ObjectId

  for record in data:
    for key, value in record.items():
      if isinstance(value, ObjectId):
        record[key] = str(value)  # Chuyển ObjectId thành chuỗi
      elif isinstance(value, datetime):
        record[key] = value.isoformat()  # Chuyển datetime thành chuỗi ISO 8601
  return data

def produce_data(topic_name):
  import json
  import time
  from kafka import KafkaProducer

  # topic_name = "enrolled_users"
  create_topic_if_not_exists(topic_name)
  print("----------- DONE: created topic")

  producer = KafkaProducer(
    bootstrap_servers=BOOSTRAP_SERVER,
    value_serializer=lambda v: json.dumps(v, default=custom_serializer).encode('utf-8')
  )
  print("----------- DONE: Connected to Kafka", producer.bootstrap_connected())

  users = prepare_data(get_enrolled_courses())
  print("----------- DONE: Get data from mongodb")

  for i in range(0, len(users), 10):
    batch = users[i:i + 10]
    
    for user in batch:
      producer.send(topic_name, user).get(timeout=30)
    print(f"Sent batch {i} of {len(batch)} users to Kafka.")

    time.sleep(1)

  producer.close()
  print("----------- DONE: Finished sending data.")

def produce_recommended_data(topic_name, recommended_users):
    import json
    import time
    from kafka import KafkaProducer

    # Hàm để tạo topic nếu chưa tồn tại (nếu cần thiết)
    create_topic_if_not_exists(topic_name)
    print(f"----------- DONE: created topic {topic_name}")

    # Kết nối Kafka producer
    producer = KafkaProducer(
        bootstrap_servers=BOOSTRAP_SERVER,
        value_serializer=lambda v: json.dumps(v, default=custom_serializer).encode('utf-8')
    )
    print(f"----------- DONE: Connected to Kafka {producer.bootstrap_connected()}")

    # Thực hiện gửi dữ liệu theo dạng batch
    for i in range(0, len(recommended_users), 10):
        batch = recommended_users[i:i + 10]
        
        for user in batch:
            # Gửi thông tin người dùng lên Kafka
            producer.send(topic_name, user).get(timeout=30)
        print(f"Sent batch {i} of {len(batch)} users to Kafka.")

        time.sleep(1)  # Để giảm tải hệ thống và đảm bảo không gửi quá nhanh

    # Đóng kết nối với Kafka producer
    producer.close()
    print("----------- DONE: Finished sending data to Kafka.")


# produce_data()