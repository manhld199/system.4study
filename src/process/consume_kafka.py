import time
import json
import pickle
import os
import networkx as nx
from pymongo import MongoClient
from kafka import KafkaConsumer, KafkaProducer
from bson.objectid import ObjectId

from models.CollaborativeFiltering import recommend_courses_cf
from models.ContentBasedFiltering import recommend_courses_cbf
from models.FactorizationMatrix import recommend_courses_fm 

BOOSTRAP_SERVER = 'kafka:29092'

# Lấy đường dẫn tuyệt đối từ đường dẫn tương đối
course_id_map_path = "/opt/airflow/data/mapping/course-id-map.json"
user_id_map_path = "/opt/airflow/data/mapping/user-id-map.json"

# Đọc file JSON và tạo dictionary đảo ngược
with open(course_id_map_path, "r") as file:
  course_id_mapping = json.load(file)

# Đọc file JSON và tạo dictionary đảo ngược
with open(user_id_map_path, "r") as file:
  user_id_mapping = json.load(file)

# Đảo ngược dictionary: {value: key}
reversed_course_mapping = {v: k for k, v in course_id_mapping.items()}
reversed_user_mapping = {v: k for k, v in user_id_mapping.items()}

def map_course_id(course_id):
  mapped_id = course_id_mapping.get(course_id)
  if mapped_id:
    return mapped_id
  
  # Tìm ngược lại course code -> ObjectId
  return reversed_course_mapping.get(course_id, None)

def map_user_id(user_id):
  mapped_id = user_id_mapping.get(user_id)
  if mapped_id:
    return mapped_id
  
  # Tìm ngược lại user code -> ObjectId
  return reversed_user_mapping.get(user_id, None)

def load_best_model(model_path):
    """Tìm và tải mô hình tốt nhất dựa trên file best_model_{tên model}.pkl."""
    best_model_files = [f for f in os.listdir(model_path) if f.startswith("best_model_") and f.endswith(".pkl")]
    if not best_model_files:
        raise FileNotFoundError("Không tìm thấy bất kỳ mô hình nào trong thư mục!")

    best_model_path = os.path.join(model_path, best_model_files[0])  # Lấy model đầu tiên (hoặc sửa theo thứ tự ưu tiên)
    with open(best_model_path, "rb") as f:
        best_model = pickle.load(f)
    best_model['model_name'] = best_model_files[0].replace("best_model_", "").replace(".pkl", "")
    return best_model

def stream_data(in_topic_name, out_topic_name, model_path, graph_path):
    consumer = KafkaConsumer(
        in_topic_name,
        bootstrap_servers=BOOSTRAP_SERVER,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    print(f"Subscribed to Kafka topic {in_topic_name}", consumer.bootstrap_connected())

    # Load the best model
    best_model = load_best_model(model_path)

    G = nx.read_gexf(graph_path)

    # Determine model type and prepare for recommendations
    model_name = best_model.get("model_name")
    if model_name == "cf":
        user_course_matrix = best_model.get("user_item_matrix")
        item_similarity_df = best_model.get("item_similarity_df")
    elif model_name == "cbf":
        similarity_matrix = best_model.get("similarity_matrix")
    elif model_name == "fm":
        predicted_scores = best_model.get("predicted_scores")
        interaction_matrix = best_model.get("interaction_matrix")
    else:
        raise ValueError(f"Unsupported model type: {model_name}")

    # Khởi tạo Kafka producer để gửi dữ liệu lên topic recommended_users
    producer = KafkaProducer(
        bootstrap_servers=BOOSTRAP_SERVER,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print(f"Connected to Kafka {producer.bootstrap_connected()}")


    # Listen for Kafka messages
    for message in consumer:
        user_data = message.value
        user_id = user_data.get("user_id")
        list_courses = user_data.get("list_courses", [])

        # Map user and course IDs
        mapped_user_id = map_user_id(user_id)
        # print("user_id", user_id, mapped_user_id)
        mapped_courses = [map_course_id(course.get("course_id")) for course in list_courses]

        # Generate recommendations
        if model_name == "cf":
            trending_courses = user_course_matrix.sum(axis=0).sort_values(ascending=False).index.tolist()
            recommendations = recommend_courses_cf(mapped_user_id, user_course_matrix, item_similarity_df, trending_courses, top_n=5)
        elif model_name == "cbf":
            recommendations = recommend_courses_cbf(G, mapped_courses, similarity_matrix, mapped_user_id, top_n=5)
        elif model_name == "fm":
            recommendations = recommend_courses_fm(mapped_user_id, predicted_scores, interaction_matrix, top_n=5)
        else:
            recommendations = []

        # Map recommended course IDs back to original IDs
        mapped_recommendations = [map_course_id(course) for course in recommendations]

        recommended_user = {
            "user_id": user_id,
            "list_courses": mapped_recommendations
        }

        # Gửi recommended_user lên Kafka topic "recommended_users"
        producer.send(out_topic_name, recommended_user).get(timeout=30)
        print(f"Sent recommended user {user_id} to Kafka.")

    # Đóng kết nối với Kafka producer và consumer
    producer.close()
    consumer.close()
    print("Kafka producer and consumer closed.")

def consume_data(topic_name):
    # Kết nối đến MongoDB
    connection_string = "mongodb+srv://admin:admin@is353.nvhsc.mongodb.net/4study?retryWrites=true&w=majority&appName=is353"
    client = MongoClient(connection_string)
    db = client["4study"]
    user_collection = db["users"]

    # Khởi tạo Kafka consumer
    consumer = KafkaConsumer(
        topic_name,
        bootstrap_servers=BOOSTRAP_SERVER,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    print(f"Subscribed to Kafka topic {topic_name}", consumer.bootstrap_connected())

    # Lắng nghe dữ liệu từ Kafka topic và cập nhật vào MongoDB
    for message in consumer:
        recommended_user = message.value
        user_id = recommended_user.get("user_id")
        list_courses = recommended_user.get("list_courses", [])

        # Tìm người dùng trong MongoDB theo user_id
        user = user_collection.find_one({"_id": ObjectId(user_id)})

        if user:
            # Nếu người dùng tồn tại, cập nhật danh sách khóa học được đề xuất
            user_collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": {"suggested_courses": list_courses}},
                # upsert=True  # Nếu không tìm thấy user, sẽ tạo mới
            )
            print(f"User {user_id} đã được cập nhật với khóa học đề xuất.")
        else:
            # Nếu người dùng không tồn tại, có thể tạo mới hoặc báo lỗi
            print(f"User {user_id} không tồn tại trong cơ sở dữ liệu.")

    # Đóng kết nối sau khi hoàn tất
    consumer.close()
    client.close()
    print("Kafka consumer and MongoDB client closed.")
