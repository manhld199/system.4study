# # Set environment
# import sys, os
# sys.path.append(os.path.abspath("./src"))
# # print("sys.path",sys.path)

import os
import pandas as pd
import pickle
import networkx as nx
import shutil

from models.CollaborativeFiltering import evaluate_recommendations_cf
from models.ContentBasedFiltering import TFIDFCourseRecommender, evaluate_recommendations_cbf
from models.FactorizationMatrix import evaluate_recommendations_fm

def delete_old_best_models(model_path):
    """
    Xóa tất cả các file bắt đầu bằng 'best_model_' trong thư mục model_path.
    """
    for file_name in os.listdir(model_path):
        if file_name.startswith("best_model_") and file_name.endswith(".pkl"):
            file_path = os.path.join(model_path, file_name)
            os.remove(file_path)
            print(f"Đã xóa file: {file_path}")


def safe_copy(src, dst):
    """Sao chép file với kiểm tra quyền."""
    try:
        if not os.access(os.path.dirname(dst), os.W_OK):
            raise PermissionError(f"Không có quyền ghi vào thư mục: {os.path.dirname(dst)}")
        
        if os.path.exists(dst):
            os.remove(dst)  # Xóa file đích nếu tồn tại
        
        shutil.copy(src, dst)
        print(f"Copied {src} to {dst}")
    except PermissionError as e:
        print(f"Lỗi quyền truy cập: {e}")
    except Exception as e:
        print(f"Lỗi không xác định: {e}")

def compare_model(test_path, model_path, graph_path):
    test_user = pd.read_csv(test_path)
    methods = {}

    # Collaborative Filtering
    cf_path = f"{model_path}/cf.pkl"
    if os.path.exists(cf_path):
        with open(cf_path, 'rb') as f:
            mappings = pickle.load(f)
            user_item_matrix = mappings['user_item_matrix']
            item_similarity_df = mappings['item_similarity_df']

        cf_results = evaluate_recommendations_cf(test_user, user_item_matrix, item_similarity_df)
        methods['Collaborative Filtering'] = cf_results.get('ndcg@5', 0)

        for metric, value in cf_results.items():
            print(f"CF - {metric}: {value:.2f}")
        print("----------- DONE: Collaborative Filtering evaluated")
    else:
        print("CF model not found!")

    # Content Based Filtering
    if os.path.exists(graph_path):
        G = nx.read_gexf(graph_path)
        recommender = TFIDFCourseRecommender(G)
        cbf_results = evaluate_recommendations_cbf(recommender, test_user)
        methods['Content Based Filtering'] = cbf_results.get('ndcg@5', 0)

        for metric, value in cbf_results.items():
            print(f"CBF - {metric}: {value:.2f}")
        print("----------- DONE: Content Based evaluated")
    else:
        print("Graph file not found!")

    # Factorization Matrix
    fm_path = f"{model_path}/fm.pkl"
    if os.path.exists(fm_path):
        with open(fm_path, 'rb') as f:
            mappings = pickle.load(f)
            user_item_matrix = mappings['user_item_matrix']
            predicted_scores = mappings['predicted_scores']

        fm_results = evaluate_recommendations_fm(test_user, predicted_scores, user_item_matrix)
        methods['Factorization Matrix'] = fm_results.get('ndcg@5', 0)

        for metric, value in fm_results.items():
            print(f"FM - {metric}: {value:.2f}")
        print("----------- DONE: Factorization Matrix evaluated")
    else:
        print("FM model not found!")

     # Xóa các file 'best_model_' trước khi lưu file mới
    delete_old_best_models(model_path)

    # So sánh và chọn phương pháp tốt nhất
    if methods:
        best_method = max(methods, key=methods.get)
        print("\n--- So sánh NDCG ---")
        for method, ndcg in methods.items():
            print(f"{method}: NDCG@5 = {ndcg:.2f}")
        print(f"Phương pháp tốt nhất: {best_method} với NDCG@5 = {methods[best_method]:.2f}")

        # Sao chép file của mô hình tốt nhất thành best_model.pkl
        if best_method == 'Collaborative Filtering':
            safe_copy(cf_path, f"{model_path}/best_model_cf.pkl")
        elif best_method == 'Content Based Filtering':
            safe_copy(graph_path, f"{model_path}/best_model_cbf.pkl")
        elif best_method == 'Factorization Matrix':
            safe_copy(fm_path, f"{model_path}/best_model_fm.pkl")

        print(f"Model tốt nhất đã được lưu thành best_model_.pkl.")
    else:
        print("Không có model nào khả dụng để so sánh.")

# # Lấy đường dẫn tuyệt đối từ đường dẫn tương đối
# relative_path = "./data"
# absolute_path = os.path.abspath(relative_path)

# print(f"path: {absolute_path}")

# evaluate_model(f"{absolute_path}/preprocessed/test-user.csv", f"{absolute_path}/models", f"{absolute_path}/graph/graph.gexf")


  