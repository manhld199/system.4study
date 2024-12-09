def preprocess_text(text):
	import re
	from nltk.tokenize import word_tokenize
	from nltk.corpus import stopwords

	stop_words = set(stopwords.words('english'))
			
	# Kiểm tra nếu text là kiểu chuỗi, nếu không chuyển sang chuỗi rỗng
	if not isinstance(text, str):
		text = str(text)

	# Chuyển sang chữ thường
	text = text.lower()

	# Loại bỏ ký tự đặc biệt và số
	text = re.sub(r'[^a-z\s]', '', text)

	# Loại bỏ khoảng trắng dư thừa
	text = re.sub(r'\s+', ' ', text).strip()

	# Loại bỏ stop words
	tokens = word_tokenize(text)
	text = ' '.join([word for word in tokens if word not in stop_words])

	return text


def preprocess_csv(input_path, output_path):
	import pandas as pd
	import nltk
	
	# Tải các tài nguyên cần thiết
	nltk.download('stopwords')
	nltk.download('wordnet')
	nltk.download('omw-1.4')
	nltk.download('punkt')
	nltk.download('punkt_tab')

	print("----------- DONE: nltk download")

	# Đọc dữ liệu từ các file CSV
	concept_df = pd.read_csv(f"{input_path}/concept.csv")
	course_df = pd.read_csv(f"{input_path}/course.csv")
	school_df = pd.read_csv(f"{input_path}/school.csv")
	train_user = pd.read_csv(f"{input_path}/train-user.csv")
	test_user = pd.read_csv(f"{input_path}/test-user.csv")

	parent_son = pd.read_csv(
		f"{input_path}/parent-son.json",
		delimiter='\t',
		names=['parent_id', 'son_id']
	)
	prerequiste_dependency = pd.read_csv(
		f"{input_path}/prerequisite-dependency.json",
		delimiter='\t',
		names=['concept_id_1', 'concept_id_2']
	)

	print("----------- DONE: read csv")

	# Tiền xử lý dữ liệu
	concept_df['concept_name'] = concept_df['concept_name'].apply(preprocess_text)
	concept_df['concept_description'] = concept_df['concept_description'].apply(preprocess_text)

	course_df['course_name'] = course_df['course_name'].apply(preprocess_text)
	course_df['course_about'] = course_df['course_about'].apply(preprocess_text)
	course_df['course_prerequisites'] = course_df['course_prerequisites'].apply(preprocess_text)

	school_df['school_name'] = school_df['school_about'].apply(preprocess_text)
	school_df['school_about'] = school_df['school_about'].apply(preprocess_text)

	prerequiste_dependency.rename(
		columns={
			'concept_id_1': 'concept_1_id',
			'concept_id_2': 'concept_2_id'
		},
		inplace=True
	)

	print("----------- DONE: preprocess")

	# Lưu dữ liệu đã xử lý thành file CSV
	concept_df.to_csv(f"{output_path}/concept.csv", index=False)
	course_df.to_csv(f"{output_path}/course.csv", index=False)
	school_df.to_csv(f"{output_path}/school.csv", index=False)
	train_user.to_csv(f"{output_path}/train-user.csv", index=False)
	test_user.to_csv(f"{output_path}/test-user.csv", index=False)

	print("----------- DONE: save CSV files")

	# Lưu dữ liệu đã xử lý thành file JSON
	parent_son.to_json(f"{output_path}/parent-son.json", orient='records', lines=True)
	prerequiste_dependency.to_json(f"{output_path}/prerequisite-dependency.json", orient='records', lines=True)

	print("----------- DONE: save JSON files")