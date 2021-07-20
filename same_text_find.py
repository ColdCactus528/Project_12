import string
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
from nltk.corpus import stopwords
from pymongo import MongoClient

def clean_string(mas_text):
	global stopwords 
	stopword = stopwords.words('english')
	result = []
	for text in mas_text:
		text = ''.join([word for word in text if word not in string.punctuation])
		text = text.lower()
		text = ' '.join([word for word in text.split() if word not in stopword])
		result.append(text)
	
	return result

def text_to_vector(text):
	vectorizer = CountVectorizer().fit_transform(text)
	vectors = vectorizer.toarray()

	return vectors

def cosine_sim_vectors(vec_1, vec_2):
	vec_1 = vec_1.reshape(1, -1)
	vec_2 = vec_2.reshape(1, -1)
	return cosine_similarity(vec_1, vec_2)[0][0]

def convert_mas_to_sentences(text):
	mas_sentences = []
	i = 2;
	text_value = str(text)
	size = len(text_value)
	sen = ""

	while i < size-1:
		sen = sen + text_value[i]
		if (text_value[i-1] != " " and text_value[i] == "." and text_value[i+1] == " ") or (text_value[i-1] == " " and text_value[i] == "." and text_value[i+1] == " ") or (text_value[i-1] != " " and text_value[i] == "." and text_value[i+1] == "'"):
			mas_sentences.append(sen)
			sen = ""
		i = i + 1

	return mas_sentences

def write_mas_to_file(FileName, mas):
	handle = open(FileName, "w")
	for sentence in mas:
		handle.write(sentence.lstrip() + "\n")
	handle.close()

	return None

def read_value_from_file(FileName):
	mas = []
	handle = open(FileName, "r")
	for line in handle:
		line = line.rstrip()
		mas.append(line)
	
	handle.close()

	return mas

def add_two_mas_to_one(mas_0, mas_1):
	result_mas = []
	for item in mas_0: 
		result_mas.append(item)
	for line in mas_1:
		result_mas.append(line)

	return(result_mas)


client = MongoClient()
db = client.dark_content
text_content = db.content_texts
same_text = db.same_text
check = []

for item_0 in text_content.find():
	text_value_0 = item_0['text']	
	id_0 = item_0['_id']
	mod_0 = item_0['last_modified']
	mas_0 = convert_mas_to_sentences(text_value_0)
	write_mas_to_file('TEXT_2', mas_0)
	mas_sentences_0 = read_value_from_file('TEXT_2')
	length_0 = len(mas_sentences_0)
	similar = []
	flag = 0

	for item_1 in text_content.find(): 
		text_value_1 = item_1['text']
		id_1 = item_1['_id']
		mod_1 = item_1['last_modified']
		
		print(id_0, "     ", id_1)
		if id_0 == id_1:
			continue 

		mas_1 = convert_mas_to_sentences(text_value_1)
		write_mas_to_file('TEXT_3', mas_1)
		mas_sentences_1 = read_value_from_file('TEXT_3')
		length_1 = len(mas_sentences_1)
		main_mas = add_two_mas_to_one(mas_sentences_0, mas_sentences_1)
		print('')
		cleaned_text = clean_string(main_mas)
		try:
			vec_text = text_to_vector(cleaned_text)
		except ValueError:
			continue

		n = 0
		same_sentences = []
		for v_1 in vec_text:
			if n > length_0 - 1:
				break 
			m = 0
			for v_2 in vec_text:
				if m < length_0:
					m = m + 1
					continue
				sim = cosine_sim_vectors(v_1, v_2)
				if sim*100 > 70:
					count = 0
					length = len(same_sentences)
					i = 0
					while i < length:
						if same_sentences[i] == main_mas[n] and same_sentences[i+1] == main_mas[m]:
							count = 2
							break 
						i += 2
					if count == 2:
						continue
					same_sentences.append(main_mas[n])
					same_sentences.append(main_mas[m])
					print(sim*100)
					print(main_mas[n])
					print(main_mas[m])
				m = m + 1
			n =  n + 1
		check_length = length_0
		if check_length < length_1:
			check_length = length_1
		if len(same_sentences) > (check_length)/3:

			print(mas_sentences_0)
			print(len(mas_sentences_0))
			print("")
			print(mas_sentences_1)
			print(len(mas_sentences_1))
			print("")

			name_of_field = "link_of_same_text" + str(flag)
			print (name_of_field);
			index = {'_id': id_0}
			result = { "$set": {name_of_field: id_1}}
			same_text.update_one(index, result, upsert = True)
			if same_text.find({"_id": id_0}):
				print(id_0 + " " + id_1 + " updated")
				flag += 1
				print("")