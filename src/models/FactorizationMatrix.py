import pandas as pd
import networkx as nx
import numpy as np
from tqdm import tqdm
from scipy.sparse.linalg import svds

# --- Tạo ma trận tương tác từ đồ thị ---
def create_interaction_matrix_fm(G):
  """
  Tạo ma trận tương tác user-course từ đồ thị.

  Parameters:
  G (NetworkX Graph): Đồ thị chứa thông tin user và course

  Returns:
  DataFrame: Ma trận tương tác user-course
  """
  # Lấy các cạnh giữa user và course
  edges = [(u, v) for u, v, d in G.edges(data=True)
            if G.nodes[u]['type'] == 'user' and G.nodes[v]['type'] == 'course']

  # Tạo DataFrame và pivot thành ma trận
  user_course_df = pd.DataFrame(edges, columns=['user_id', 'course_id'])
  user_course_df['interaction'] = 1
  return user_course_df.pivot(
    index='user_id',
    columns='course_id',
    values='interaction'
  ).fillna(0)

# --- Matrix Factorization ---
def matrix_factorization(interaction_matrix, k=500):
  """
  Factorization ma trận tương tác bằng phương pháp SVD.

  Parameters:
  interaction_matrix (DataFrame): Ma trận tương tác user-course.
  k (int): Số chiều ẩn.

  Returns:
  np.ndarray: Ma trận user_features.
  np.ndarray: Ma trận course_features.
  """
  # Chuyển interaction matrix thành numpy array
  R = interaction_matrix.values
  user_ids = interaction_matrix.index
  course_ids = interaction_matrix.columns

  # Phân tích SVD
  user_features, sigma, course_features = svds(R, k=k)
  sigma = np.diag(sigma)

  # Trả về các ma trận đặc trưng
  return (
    pd.DataFrame(user_features @ sigma, index=user_ids),
    pd.DataFrame(course_features.T, index=course_ids)
  )

# --- Dự đoán điểm tương tác ---
def predict_interactions(user_features, course_features):
  """
  Dự đoán điểm tương tác dựa trên ma trận đặc trưng.

  Parameters:
  user_features (DataFrame): Ma trận đặc trưng người dùng.
  course_features (DataFrame): Ma trận đặc trưng khóa học.

  Returns:
  DataFrame: Ma trận dự đoán điểm tương tác.
  """
  predictions = user_features.values @ course_features.values.T
  return pd.DataFrame(predictions, index=user_features.index, columns=course_features.index)

# --- Đề xuất khóa học ---
def recommend_courses_fm(user_id, predicted_scores, interaction_matrix, top_n=5):
    if user_id not in predicted_scores.index:
        raise KeyError(f"user_id {user_id} không tồn tại trong predicted_scores")
    if user_id not in interaction_matrix.index:
        raise KeyError(f"user_id {user_id} không tồn tại trong interaction_matrix")

    user_scores = predicted_scores.loc[user_id]
    watched_courses = interaction_matrix.loc[user_id][interaction_matrix.loc[user_id] > 0].index.tolist()
    recommended_courses = user_scores.drop(watched_courses, errors='ignore').sort_values(ascending=False)

    return recommended_courses.index[:top_n].tolist()

# --- Đánh giá hệ thống ---

class RecommendationMetrics:
  """Class tính toán các metric đánh giá hệ thống khuyến nghị"""

  @staticmethod
  def precision_at_k(recommended, actual, k=5):
    recommended_k = set(recommended[:k])
    actual_set = set(actual)
    return len(recommended_k & actual_set) / k

  @staticmethod
  def recall_at_k(recommended, actual, k=5):
    recommended_k = set(recommended[:k])
    actual_set = set(actual)
    return len(recommended_k & actual_set) / len(actual_set) if len(actual_set) > 0 else 0

  @staticmethod
  def ndcg_at_k(recommended, actual, k=5):
    def dcg_at_k(recommended, actual, k):
      recommended_k = recommended[:k]
      actual_set = set(actual)
      return sum([1 / np.log2(idx + 2) for idx, rec in enumerate(recommended_k) if rec in actual_set])

    def idcg_at_k(actual, k):
      actual_count = min(len(actual), k)
      return sum([1 / np.log2(idx + 2) for idx in range(actual_count)])

    dcg = dcg_at_k(recommended, actual, k)
    idcg = idcg_at_k(actual, k)
    return dcg / idcg if idcg > 0 else 0

  @staticmethod
  def hit_rate_at_k(recommended, actual, k=5):
    """Tính tỷ lệ hit (có ít nhất 1 khóa học trong top-k đề xuất)"""
    return 1 if any(course in recommended[:k] for course in actual) else 0


def evaluate_recommendations_fm(test_user, predicted_scores, interaction_matrix, k=5):
  """
  Đánh giá hệ thống khuyến nghị trên tập test.

  Parameters:
  test_user (DataFrame): DataFrame chứa thông tin test.
  predicted_scores (DataFrame): Ma trận dự đoán điểm tương tác.
  interaction_matrix (DataFrame): Ma trận tương tác user-course.
  k (int): Số lượng khóa học được đề xuất.

  Returns:
  dict: Kết quả các metrics.
  """
  # Lọc test_user để chỉ giữ lại các user có trong predicted_scores
  valid_users = set(predicted_scores.index) & set(test_user['user_id'])
  filtered_test_user = test_user[test_user['user_id'].isin(valid_users)]

  if filtered_test_user.empty:
    print("Không có người dùng hợp lệ trong test_user để đánh giá.")
    return {}

  metrics = RecommendationMetrics()
  precisions, recalls, ndcgs, hit_rates = [], [], [], []

  for _, row in tqdm(filtered_test_user.iterrows(), total=len(filtered_test_user), desc="Evaluating"):
    user_id = row['user_id']
    actual_courses = [row['course_id']]

    try:
      # Lấy danh sách đề xuất cho user_id
      recommended = recommend_courses_fm(user_id, predicted_scores, interaction_matrix, top_n=k)
    except KeyError as e:
      print(f"Bỏ qua user_id {user_id} do lỗi: {e}")
      continue

    # Tính các metric
    precisions.append(metrics.precision_at_k(recommended, actual_courses, k))
    recalls.append(metrics.recall_at_k(recommended, actual_courses, k))
    ndcgs.append(metrics.ndcg_at_k(recommended, actual_courses, k))
    hit_rates.append(metrics.hit_rate_at_k(recommended, actual_courses, k))

  # Nếu không có user nào được đánh giá, trả về thông báo lỗi
  if not precisions or not recalls or not ndcgs or not hit_rates:
    print("Không có đủ dữ liệu để tính toán các metrics.")
    return {}

  return {
    f'precision@{k}': np.mean(precisions),
    f'recall@{k}': np.mean(recalls),
    f'hit_rate@{k}': np.mean(hit_rates),
    f'ndcg@{k}': np.mean(ndcgs),
  }

