from pymongo import MongoClient 

# Сравнение хэша
def compare_hash_piece(hash1, hash2):
    l = len(hash1)
    i = 0
    count = 0
    while i < l:
        if hash1[i] != hash2[i]:
            count = count + 1
        i = i + 1
    return count

def compare_hash(mas_image_hash_1, mas_image_hash_2):
	num_of_dif = 0
	i = 0
	while i < 9:
		hash_1 = mas_image_hash_1[i]
		hash_2 = mas_image_hash_2[i]
		count = compare_hash_piece(hash_1, hash_2)
		num_of_dif += count		
		i += 1
	return num_of_dif




client = MongoClient()
db = client.dark_content
z = 0
same_links = []
same_pictures = db.same_pictures

for image in db.images_with_hash.find():
	image_url_0 = image['_id']
	url_0 = image['url_from_page']
	number_0 = image_url_0.find('.gif')
	num_0 = image_url_0.find('.png')

	if number_0 != -1:
		continue
	if num_0 != -1:
		continue

	width_0, high_0 = image['size']

	if (width_0 < 400) or (high_0 < 400):
		continue

	hash_im_0 = image['has_im']
	hash_im_mirr_0 = image['hash_im_mirr']
	hash_im_mirr_flip_0 = image['hash_im_mirr_flip']
	hash_im_flip_0 = image['hash_im_flip']

	flag = 0
	for item in db.images_with_hash.find():
		if (flag > 100):
			break
		image_url_1 = item['_id']
		url_1 = item['url_from_page']
		number_1 = image_url_1.find('.gif')
		num_1 = image_url_1.find('.png')

		if (image_url_1 == image_url_0):
			continue
		if (url_1 == url_0):
			continue
		if number_1 != -1:
			continue
		if num_1 != -1:
			continue

		width_1, high_1 = image['size']

		if (width_1 < 400) or (high_1 < 400):
			continue
		
		hash_im_1 = item['has_im']
		hash_im_mirr_1 = item['hash_im_mirr']
		hash_im_mirr_flip_1 = item['hash_im_mirr_flip']
		hash_im_flip_1 = item['hash_im_flip']

		number = 1000
		n_0 = compare_hash(hash_im_1, hash_im_0)
		n_1 = compare_hash(hash_im_mirr_1, hash_im_mirr_0)
		n_2 = compare_hash(hash_im_mirr_flip_1, hash_im_mirr_flip_0)
		n_3 = compare_hash(hash_im_flip_1, hash_im_flip_0)

		if number > n_0:
			number =  n_0
		if number > n_1:
			number =  n_0
		if number > n_2:
			number =  n_2
		if number > n_3:
			number =  n_3

		if (number >= 0) and (number < 80):

			k = 0
			flag_raise = 0
			while k < len(same_links):
				if (image_url_0 == same_links[k]) and (image_url_1 == same_links[k+1]):
					flag_raise = 1
					break
				k += 3
			
			if flag_raise == 0 : 		
				same_links.append(image_url_0)
				same_links.append(image_url_1)
				same_links.append(number)
				
				name_of_field = "link_of_same_picture" + str(flag)
				print (name_of_field);
				index = {'_id': url_0}
				result = { "$set": {name_of_field: url_1}}
				same_pictures.update_one(index, result, upsert = True)
				if same_pictures.find({"_id": url_0}):
					print(image_url_0 + " " + image_url_1 + " updated")
					flag = flag + 1
					print("")

	