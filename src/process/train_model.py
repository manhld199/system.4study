# # Set environment
# import sys, os


# sys.path.append(os.path.abspath("./src"))
# # print("sys.path",sys.path)

def train_cf(graph_path, model_path):
  import pickle
  import networkx as nx
  from models.CollaborativeFiltering import compute_similarity_matrices, create_interaction_matrix_cf

  print("----------- START: Collaborative Filtering")
  # Load đồ thị
  G = nx.read_gexf(graph_path)
  print("----------- DONE: Loaded graph")
  
  # Tạo ma trận tương tác
  user_item_matrix = create_interaction_matrix_cf(G)
  print("----------- DONE: created interaction matrix")

  # Tính ma trận tương đồng
  user_similarity_df, item_similarity_df = compute_similarity_matrices(user_item_matrix)
  print("----------- DONE: create similarity matrix")
  
  # print(f"user_similarity_df: {user_similarity_df.head()}")
  # print(f"item_similarity_df: {item_similarity_df.head()}")

  # Lưu user_mapping và course_mapping
  with open(f"{model_path}/cf.pkl", 'wb') as f:
      pickle.dump({'user_item_matrix': user_item_matrix, 
                  'item_similarity_df': item_similarity_df}, f)
  
  print("----------- DONE: Collaborative Filtering saved")

def train_cbf(graph_path, model_path):
  import pickle
  import networkx as nx
  from models.ContentBasedFiltering import TFIDFCourseRecommender

  # Load đồ thị
  G = nx.read_gexf(graph_path)
  
  recommender = TFIDFCourseRecommender(G)
  
  # print(f"TFIDFCourseRecommender: {recommender.similarity_matrix}")

  # Lưu user_mapping và course_mapping
  with open(f"{model_path}/cbf.pkl", 'wb') as f:
          pickle.dump({'similarity_matrix': recommender.similarity_matrix}, f)
  
  print("----------- DONE: Content-based Filtering saved")

def train_fm(graph_path, model_path):
  import pickle
  import networkx as nx
  from models.FactorizationMatrix import create_interaction_matrix_fm, matrix_factorization, predict_interactions

  # Load đồ thị
  G = nx.read_gexf(graph_path)

  user_item_matrix = create_interaction_matrix_fm(G)
  user_features, course_features = matrix_factorization(user_item_matrix, k=5)
  predicted_scores = predict_interactions(user_features, course_features)

  # Lưu user_mapping và course_mapping
  with open(f"{model_path}/fm.pkl", 'wb') as f:
    pickle.dump({'user_item_matrix': user_item_matrix, 
            'predicted_scores': predicted_scores}, f)

  print("----------- DONE: Factorization Matrix saved")


# # Lấy đường dẫn tuyệt đối từ đường dẫn tương đối
# relative_path = "./data"
# absolute_path = os.path.abspath(relative_path)

# print(f"path: {absolute_path}")

# train_cf(f"{absolute_path}/graph/graph.gexf", f"{absolute_path}/models")
# train_cbf(f"{absolute_path}/graph/graph.gexf", f"{absolute_path}/models")
# train_fm(f"{absolute_path}/graph/graph.gexf", f"{absolute_path}/models")