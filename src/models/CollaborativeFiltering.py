from tqdm import tqdm
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def create_interaction_matrix_cf(G):
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

def compute_similarity_matrices(user_item_matrix):
  """
  Tính ma trận độ tương đồng cho users và courses.
  
  Parameters:
  user_item_matrix (DataFrame): Ma trận tương tác user-course
  
  Returns:
  tuple: (user_similarity_df, item_similarity_df)
  """

  # Tính độ tương đồng cosine
  user_similarity = cosine_similarity(user_item_matrix)
  item_similarity = cosine_similarity(user_item_matrix.T)
  
  # Chuyển về DataFrame với index và columns phù hợp
  user_similarity_df = pd.DataFrame(
      user_similarity,
      index=user_item_matrix.index,
      columns=user_item_matrix.index
  )
  item_similarity_df = pd.DataFrame(
      item_similarity,
      index=user_item_matrix.columns,
      columns=user_item_matrix.columns
  )
  
  return user_similarity_df, item_similarity_df

def recommend_courses_cf(user_id, user_course_matrix, item_similarity_df, trending_courses, top_n):
    """
    Đề xuất khóa học cho một user cụ thể.
    
    Parameters:
    user_id: ID của user cần đề xuất
    user_course_matrix (DataFrame): Ma trận tương tác user-course
    item_similarity_df (DataFrame): Ma trận độ tương đồng giữa các khóa học
    top_n (int): Số lượng khóa học cần đề xuất
    
    Returns:
    list: Danh sách các khóa học được đề xuất
    """
    # Kiểm tra nếu user_id không tồn tại
    if user_id not in user_course_matrix.index:
        # print(f"User {user_id} không tồn tại trong dữ liệu, đề xuất các khóa học thịnh hành.")
        return trending_courses[:top_n]
    
    # Lấy các khóa học đã học
    user_courses = user_course_matrix.loc[user_id]
    watched_courses = user_courses[user_courses > 0].index.tolist()
    
    # Tính điểm khuyến nghị
    course_scores = {}
    for course in watched_courses:
        similar_courses = item_similarity_df[course].sort_values(ascending=False).index
        for sim_course in similar_courses:
            if sim_course not in watched_courses:
                similarity_score = item_similarity_df.loc[course, sim_course]
                course_scores[sim_course] = course_scores.get(sim_course, 0) + similarity_score
    
    # Lấy top N khóa học
    recommended_courses = sorted(
        course_scores.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:top_n]
    
    return [course[0] for course in recommended_courses]

class RecommendationMetrics:
  """Class tính toán các metric đánh giá hệ thống khuyến nghị"""
  
  @staticmethod
  def precision_at_k(recommended, actual, k):
    """Tính Precision@k"""
    recommended_k = set(recommended[:k])
    actual_set = set(actual)
    return len(recommended_k & actual_set) / k
  
  @staticmethod
  def recall_at_k(recommended, actual, k):
    """Tính Recall@k"""
    recommended_k = set(recommended[:k])
    actual_set = set(actual)
    return len(recommended_k & actual_set) / len(actual_set) if len(actual_set) > 0 else 0
  
  @staticmethod
  def hit_rate_at_k(recommended, actual, k):
    """Tính Hit Rate@k"""
    recommended_k = set(recommended[:k])
    actual_set = set(actual)
    return 1 if len(recommended_k & actual_set) > 0 else 0
  
  @staticmethod
  def ndcg_at_k(recommended, actual, k):
    """Tính NDCG@k"""
    def dcg_at_k(recommended, actual, k):
      recommended_k = recommended[:k]
      actual_set = set(actual)
      return sum([1 / np.log2(idx + 2) for idx, rec in enumerate(recommended_k) 
                  if rec in actual_set])
        
    def idcg_at_k(actual, k):
      actual_count = min(len(actual), k)
      return sum([1 / np.log2(idx + 2) for idx in range(actual_count)])
        
    dcg = dcg_at_k(recommended, actual, k)
    idcg = idcg_at_k(actual, k)
    return dcg / idcg if idcg > 0 else 0

def evaluate_recommendations_cf(test_user, user_item_matrix, item_similarity_df, k=5):
  """
  Đánh giá hệ thống khuyến nghị trên tập test.
  
  Parameters:
  test_user (DataFrame): DataFrame chứa thông tin test
  user_item_matrix (DataFrame): Ma trận tương tác user-course
  item_similarity_df (DataFrame): Ma trận độ tương đồng giữa các khóa học
  k (int): Số lượng khóa học được đề xuất
  
  Returns:
  dict: Kết quả các metrics
  """

  # Generate recommendations
  recommendations = {}
  for user_id in tqdm(test_user['user_id'], desc="Generating recommendations"):
      trending_courses = user_item_matrix.sum(axis=0).sort_values(ascending=False).index.tolist()
      recommendations[user_id] = recommend_courses_cf(
          user_id, user_item_matrix, item_similarity_df, trending_courses, k
      )
  test_user['recommended_courses'] = test_user['user_id'].map(recommendations)
  
  # Calculate metrics
  metrics = RecommendationMetrics()
  test_user['precision'] = test_user.apply(
      lambda x: metrics.precision_at_k(x['recommended_courses'], [x['course_id']], k), 
      axis=1
  )
  test_user['recall'] = test_user.apply(
      lambda x: metrics.recall_at_k(x['recommended_courses'], [x['course_id']], k), 
      axis=1
  )
  test_user['hit_rate'] = test_user.apply(
      lambda x: metrics.hit_rate_at_k(x['recommended_courses'], [x['course_id']], k), 
      axis=1
  )
  test_user['ndcg'] = test_user.apply(
      lambda x: metrics.ndcg_at_k(x['recommended_courses'], [x['course_id']], k), 
      axis=1
  )
  
  # Calculate mean metrics
  results = {
      f'precision@{k}': test_user['precision'].mean(),
      f'recall@{k}': test_user['recall'].mean(),
      f'hit_rate@{k}': test_user['hit_rate'].mean(),
      f'ndcg@{k}': test_user['ndcg'].mean()
  }
  
  return results