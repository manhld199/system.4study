import networkx as nx
import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy.sparse import csr_matrix
from functools import lru_cache

class TFIDFCourseRecommender:
  def __init__(self, G):
    self.G = G
    # Cache đặc trưng của các khóa học
    self.similarity_matrix = {}
    
    # TF-IDF Vectorizers với cấu hình chi tiết
    self.concept_vectorizer = TfidfVectorizer(
      max_features=500,
      stop_words='english',
      ngram_range=(1, 2)
    )
    self.school_vectorizer = TfidfVectorizer(
      max_features=300,
      stop_words='english',
      ngram_range=(1, 2)
    )
    self.text_vectorizer = TfidfVectorizer(
      max_features=1000,
      stop_words='english',
      ngram_range=(1, 2)
    )
    
    # Khởi tạo cache
    self._initialize_caches()
      
  def _initialize_caches(self):
    """Khởi tạo cache cho đặc trưng khóa học và ma trận similarity"""
    print("Đang khởi tạo cache...")
    
    # Lấy tất cả các khóa học
    all_courses = [n for n in self.G.nodes() if self.G.nodes[n]['type'] == 'course']
    
    # Chuẩn bị dữ liệu cho TF-IDF
    concept_docs, school_docs, text_docs, course_ids = [], [], [], []
    
    print("Đang chuẩn bị dữ liệu cho TF-IDF...")
    for course in tqdm(all_courses, desc="Xử lý đặc trưng khóa học"):
      # Lấy thông tin concept
      concept_details = [f"{self.G.nodes[n]['concept_name']} {self.G.nodes[n].get('concept_about', '')}" 
                          for n in self.G.neighbors(course) 
                          if self.G.nodes[n]['type'] == 'concept']
      
      # Lấy thông tin school
      school_details = [f"{self.G.nodes[n]['school_name']} {self.G.nodes[n].get('school_about', '')}" 
                        for n in self.G.neighbors(course) 
                        if self.G.nodes[n]['type'] == 'school']
      
      # Kết hợp tất cả thông tin
      text_content = ' '.join([
        self.G.nodes[course]['course_name'], 
        self.G.nodes[course]['course_about'], 
        self.G.nodes[course]['course_prerequisites']
      ])
      
      concept_docs.append(' '.join(concept_details))
      school_docs.append(' '.join(school_details))
      text_docs.append(text_content)
      course_ids.append(course)
        
    print("Đang tính toán TF-IDF vectors...")
    # Tính TF-IDF cho concepts, schools và text với sparse matrix
    concept_tfidf = self.concept_vectorizer.fit_transform(concept_docs)
    school_tfidf = self.school_vectorizer.fit_transform(school_docs)
    text_tfidf = self.text_vectorizer.fit_transform(text_docs)
    
    # Tính similarity matrix kết hợp
    print("Đang tính toán ma trận similarity...")
    concept_sim = cosine_similarity(concept_tfidf)
    school_sim = cosine_similarity(school_tfidf)
    text_sim = cosine_similarity(text_tfidf)
    
    combined_sim = (
      0.3 * concept_sim + 
      0.2 * school_sim + 
      0.5 * text_sim
    )
    combined_sim = csr_matrix(combined_sim)  # Chuyển thành sparse matrix để tiết kiệm bộ nhớ
    
    # Lưu vào similarity matrix
    for i, course1 in enumerate(course_ids):
      for j, course2 in enumerate(course_ids):
        if combined_sim[i, j] > 0.1:  # Chỉ lưu các giá trị similarity lớn hơn ngưỡng
          self.similarity_matrix[(course1, course2)] = combined_sim[i, j]
      
    print("Hoàn thành khởi tạo cache!")
    
  @lru_cache(maxsize=None)
  def get_similarity(self, course1, course2):
    """Lấy độ tương đồng giữa hai khóa học từ cache."""
    return self.similarity_matrix.get((course1, course2), 0)
  
  def get_recommendations(self, user_id, n=5):
    """Lấy n khóa học được khuyến nghị cho user."""
    user_courses = [n for n in self.G.neighbors(str(user_id)) 
                    if self.G.nodes[n]['type'] == 'course']
    
    all_courses = set(course for course, *_ in self.similarity_matrix.keys())
    candidate_courses = all_courses - set(user_courses)
    
    course_scores = {}
    for target_course in candidate_courses:
      similarities = [self.get_similarity(target_course, uc) for uc in user_courses]
      course_scores[target_course] = np.mean(similarities) if similarities else 0
    
    recommended_courses = sorted(course_scores.items(), key=lambda x: x[1], reverse=True)[:n]
    return [course for course, score in recommended_courses]
  
def get_similarity(course1, course2, similarity_matrix):
    """Lấy độ tương đồng giữa hai khóa học từ cache."""
    return similarity_matrix.get((course1, course2), 0)


def recommend_courses_cbf(G, learn_course, similarity_matrix, user_id, top_n=5):
    user_courses = learn_course
    all_courses = set(course for course, *_ in similarity_matrix.keys())
    candidate_courses = all_courses - set(user_courses)

    course_scores = {}
    for target_course in candidate_courses:
        similarities = [get_similarity(target_course, uc, similarity_matrix) for uc in user_courses]
        course_scores[target_course] = np.mean(similarities) if similarities else 0

    recommended_courses = sorted(course_scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return [course for course, score in recommended_courses]

def evaluate_recommendations_cbf(recommender, test_data, k=5):
  """Đánh giá hệ thống khuyến nghị với các metric."""
  hits, precision_sum, recall_sum, ndcg_sum = 0, 0, 0, 0
  unique_users = test_data['user_id'].unique()
  total_users = len(unique_users)
  
  progress_bar = tqdm(unique_users, desc="Đánh giá khuyến nghị", unit="user")
  
  for user_id in progress_bar:
    actual_courses = set(test_data[test_data['user_id'] == user_id]['course_id'].astype(str))
    recommended_courses = recommender.get_recommendations(str(user_id), n=k)
    
    if any(course in actual_courses for course in recommended_courses):
      hits += 1
    
    relevant_and_recommended = len(set(recommended_courses).intersection(actual_courses))
    precision = relevant_and_recommended / k
    recall = relevant_and_recommended / len(actual_courses)
    
    precision_sum += precision
    recall_sum += recall
    
    dcg, idcg = 0, 0
    for i, course in enumerate(recommended_courses):
      rel = 1 if course in actual_courses else 0
      dcg += rel / np.log2(i + 2)
    
    for i in range(min(k, len(actual_courses))):
      idcg += 1 / np.log2(i + 2)
    
    ndcg = dcg / idcg if idcg > 0 else 0
    ndcg_sum += ndcg
    
    progress_bar.set_postfix({
      'Hit Rate': f"{hits/total_users:.4f}",
      'Precision': f"{precision_sum/total_users:.4f}"
    })
  
  metrics = {
    'hit_rate@k': hits / total_users,
    'precision@k': precision_sum / total_users,
    'recall@k': recall_sum / total_users,
    'ndcg@k': ndcg_sum / total_users
  }
  
  return metrics

def evaluate_recommender(G, test_data, k=5):
  """Chạy đánh giá hệ thống khuyến nghị."""
  print(f"Khởi tạo hệ thống khuyến nghị với k={k}...")
  
  # Khởi tạo recommender
  recommender = TFIDFCourseRecommender(G)
  
  # Đánh giá
  print("\nBắt đầu đánh giá...")
  metrics = evaluate_recommendations_cbf(recommender, test_data, k)
  
  print("\nKết quả cuối cùng:")
  print(f"Hit Rate@{k}: {metrics['hit_rate@k']:.4f}")
  print(f"Precision@{k}: {metrics['precision@k']:.4f}")
  print(f"Recall@{k}: {metrics['recall@k']:.4f}")
  print(f"NDCG@{k}: {metrics['ndcg@k']:.4f}")
  
  return metrics