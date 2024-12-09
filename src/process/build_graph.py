# Hàm thêm nút với tiến trình
def add_nodes_with_progress(G, df, node_type, color_map, desc, **kwargs):
  from tqdm import tqdm

  progress_bar = tqdm(total=len(df), desc=desc)

  for _, row in df.iterrows():
    node_id = str(row[f'{node_type}_id'])
    node_attrs = {
      'type': node_type,
      'color': color_map.get(node_type, 'lightgrey')
    }

    # Thêm các thuộc tính bổ sung
    for key, value in kwargs.items():
      if value in row.index:
        node_attrs[key] = row[value]

    G.add_node(node_id, **node_attrs)
    progress_bar.update(1)

  progress_bar.close()

# Hàm thêm cạnh với tiến trình
def add_edges_with_progress(G, df, source_type, target_type, desc):
  from tqdm import tqdm

  progress_bar = tqdm(total=len(df), desc=desc)

  valid_nodes = set(G.nodes())
  edges = []

  for _, row in df.iterrows():
    source_id = str(row[f'{source_type}_id'])
    target_id = str(row[f'{target_type}_id'])

    if source_id in valid_nodes and target_id in valid_nodes:
      edges.append((source_id, target_id))

    progress_bar.update(1)

  G.add_edges_from(edges)
  progress_bar.close()

def build_graph(input_path, output_path):
  import pandas as pd
  import networkx as nx

  # Tạo đồ thị
  G = nx.Graph()
 
  # Bảng màu cho các loại nút
  color_map = {
    'user': 'lightgreen',
    'concept': 'lightcoral',
    'school': 'lightgrey',
    'course': 'plum'
  }

  # Đọc dữ liệu từ các file CSV
  concept_df = pd.read_csv(f"{input_path}/concept.csv")
  course_df = pd.read_csv(f"{input_path}/course.csv")
  school_df = pd.read_csv(f"{input_path}/school.csv")
  train_user = pd.read_csv(f"{input_path}/train-user.csv")

  parent_son = pd.read_csv(
    f"{input_path}/parent-son.json",
    delimiter='\t',
    names=['parent_id', 'son_id']
  )
  prerequiste_dependency = pd.read_csv(
    f"{input_path}/prerequisite-dependency.json",
    delimiter='\t',
    names=['concept_1_id', 'concept_2_id']
  )

  # Thêm nút User
  add_nodes_with_progress(
    G,
    train_user.drop_duplicates(subset=['user_id']),
    'user',
    color_map,
    "Adding user nodes",
    user_name='user_name'
  )

  # Thêm nút Concept
  add_nodes_with_progress(
    G,
    concept_df,
    'concept',
    color_map,
    "Adding concept nodes",
    concept_name='concept_name',
    concept_description='concept_description'
  )

  # Thêm nút School
  add_nodes_with_progress(
    G,
    school_df.drop_duplicates(subset=['school_id']),
    'school',
    color_map,
    "Adding school nodes",
    school_name='school_name',
    school_about='school_about'
  )

  # Thêm nút Course
  add_nodes_with_progress(
    G,
    course_df,
    'course',
    color_map,
    "Adding course nodes",
    course_name='course_name',
    course_about='course_about',
    course_prerequisites='course_prerequisites'
  )

  # Thêm cạnh Course-Concept
  add_edges_with_progress(
    G,
    concept_df,
    'course',
    'concept',
    "Adding edges between courses and concepts"
  )

  # Thêm cạnh Course-School
  add_edges_with_progress(
    G,
    school_df,
    'school',
    'course',
    "Adding edges between schools and courses"
  )

  # Thêm cạnh Course-User
  add_edges_with_progress(
    G,
    train_user,
    'user',
    'course',
    "Adding edges between users and courses"
  )

  # Thêm cạnh Parent-Son
  add_edges_with_progress(
    G,
    parent_son,
    'parent',
    'son',
    "Adding parent-son edges"
  )

  # Thêm cạnh Prerequisite Dependency
  add_edges_with_progress(
    G,
    prerequiste_dependency,
    'concept_1',
    'concept_2',
    "Adding prerequisite dependencies"
  )

  # In thống kê đồ thị
  print(f"Tổng số nút: {G.number_of_nodes()}")
  print(f"Tổng số cạnh: {G.number_of_edges()}")

  # Lưu đồ thị
  nx.write_gexf(G, f"{output_path}/graph.gexf")  # Lưu dưới dạng GEXF
  print("----------- DONE: save graph files")

# import os

# # Lấy đường dẫn tuyệt đối từ đường dẫn tương đối
# relative_path = "./data"
# absolute_path = os.path.abspath(relative_path)

# print(f"path: {absolute_path}")

# build_graph(f"{absolute_path}/preprocessed", f"{absolute_path}/graph")