from pymongo import MongoClient 
import requests
import os
import time
import json
from bs4 import BeautifulSoup
import datetime 
import image_slicer
import cv2
import difflib
from PIL import Image, ImageOps
import time
import os
from io import BytesIO
from PIL import ImageFile

def renaming(FileName, value):
	count = len(FileName)
	i = FileName.find(".")
	expansion = FileName[i:count]
	new_name = FileName[:i] + value + expansion
	return new_name

def mirror_image(FileName):
	im = Image.open(FileName)
	im_mirr = ImageOps.mirror(im)
	new_name = renaming(FileName, "_mirr")
	im_mirr.save(new_name)
	im.close()
	return(new_name)

def flip_mirr_image(FileName):
	im = Image.open(FileName)
	im_mirr = ImageOps.mirror(im)
	im_flip = ImageOps.flip(im_mirr)
	new_name = renaming(FileName, "_mirr_flip")
	im_flip.save(new_name)
	im.close()
	return(new_name)

def flip_image(FileName):
	im = Image.open(FileName)
	im_flip = ImageOps.flip(im)
	new_name = renaming(FileName, "_flip")
	im_flip.save(new_name)
	im.close()
	return(new_name)

# Удаление файла 
def delete_file(FileName):
	if os.path.exists(FileName):
		os.remove(FileName)
	else:
		print("The " + FileName + " does not exist")
	return None

def resize_pic_24_24(FileName):
	pic = Image.open(FileName)
	resized = pic.resize((24,24), Image.ANTIALIAS)
	new_name = renaming(FileName, "_res")
	resized.save(new_name)
	pic.close()
	return new_name

def slicer(name):
	tiles = image_slicer.slice(name,9)
	delete_file(name)
	images = []
	x = 1 
	while x <= 3:
		y = 1
		while y <= 3:
			line = name[:name.find("_res") + 4] + ("_0") + str(x) + ("_0") + str(y) + ".png"
			images.append(line)
			y += 1 
		x += 1
	return images

def images_hash(FileName):
	resized = resize_pic_24_24(FileName)
	images = slicer(resized)
	ims_hash = []
	for im in images:
		pic = cv2.imread(im)
		g_image = cv2.cvtColor(pic, cv2.COLOR_BGR2GRAY)
		avg = g_image.mean() #Среднее значение пикселя
		ret, threshold_image = cv2.threshold(g_image, avg, 255, 0) #Бинаризация по порогу

		# Рассчет хэша
		_hash = ""
		for x in range(8):
			for y in range(8):
				val = threshold_image[x,y]
				if val == 255:
					_hash = _hash + "1"
				else:
					_hash = _hash + "0"
		ims_hash.append(_hash)

	for pic in images:
		delete_file(pic)

	return ims_hash

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

def analyseImage(path):
    im = Image.open(path)
    results = {
        'size': im.size,
        'mode': 'full',
    }
    try:
        while True:
            if im.tile:
                tile = im.tile[0]
                update_region = tile[1]
                update_region_dimensions = update_region[2:]
                if update_region_dimensions != im.size:
                    results['mode'] = 'partial'
                    break
            im.seek(im.tell() + 1)
    except EOFError:
        pass
    return results


def processImage(path):
    mode = analyseImage(path)['mode']
    im = Image.open(path)
    i = 0
    p = im.getpalette()
    last_frame = im.convert('RGBA')
    im_names = []
    
    try:
        while True:
            if not im.getpalette():
                im.putpalette(p)
            
            new_frame = Image.new('RGBA', im.size)
            if mode == 'partial':
                new_frame.paste(last_frame)
            
            new_frame.paste(im, (0,0), im.convert('RGBA'))
            name = '%s-%d.png' % (''.join(os.path.basename(path).split('.')[:-1]), i)
            im_names.append(name)
            new_frame.save('%s-%d.png' % (''.join(os.path.basename(path).split('.')[:-1]), i), 'PNG')

            i += 1
            last_frame = new_frame
            im.seek(im.tell() + 1)
        return im_names
    except EOFError:
        pass

    return im_names

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

def image_size(FileName):
	im = Image.open(FileName)
	result = im.size
	im.close()
	return result

client = MongoClient()
db = client.dark_content
content_images = db.content_images
images_with_hash = db.images_with_hash
images_hash_was_taken = db.images_hash_was_taken
ImageFile.LOAD_TRUNCATED_IMAGES = True

for link in db.content_images.find():
	image_url = link['_id']
	url = link['url_from_page']
	mod = link['last_modified']
	image_bytes = link['image_bytes']

	line = image_url[image_url.rfind(".")+1:len(image_url)]
	if (line.rfind("png") != -1) or (line.rfind("jpg") != -1):
		line = line[:3]
		flag = image_url.rfind(line) + 3
		image_url = image_url[:flag]
		print(image_url)
	if line.rfind("jpeg") != -1:
		line = line[:4]
		flag = image_url.rfind(line) + 4
		image_url = image_url[:flag]
		print(image_url)
	expansion = line.lower()

	mas = []
	name_im = ("")
	name_im_mir = ("")
	name_im_mirr_flip = ("")
	name_im_flip = ("")
	try:
		if (expansion == "png") or (expansion == "jpg") or (expansion == "jpeg"):
			name_im = image_url[image_url.rfind("/")+1:len(image_url)].lower()
			# image = BytesIO(link['image_bytes'])
			# pic = Image.open(image)
			# pic.save(name_im)

			handle = open(name_im,"wb")
			handle.write(link['image_bytes'])
			handle.close()

			image_proportions = image_size(name_im)

			name_im_mir = mirror_image(name_im)
			name_im_mirr_flip = flip_mirr_image(name_im)
			name_im_flip = flip_image(name_im)

			first = images_hash(name_im)
			second = images_hash(name_im_mir)
			third = images_hash(name_im_mirr_flip)
			fourth = images_hash(name_im_flip)

			index = {'_id': image_url}
			result = { "$set": {'url_from_page': url, 'size': image_proportions, 'has_im': first, 'hash_im_mirr': second, 'hash_im_mirr_flip': third, 'hash_im_flip': fourth, 'last_modified_in_db': mod}}
			db.images_with_hash.update_one(index, result, upsert = True)
			if db.images_with_hash.find({"_id": image_url}):
				print(image_url + " updated")

			idetif = {'_id': image_url}
			new_item = { "$set": {'url_from_page': url, 'image_bytes': image_bytes, "last_modified": mod}}
			db.images_hash_was_taken.update_one( idetif, new_item, upsert = True)
			db.content_images.delete_one(link)

			delete_file(name_im)
			delete_file(name_im_mir)
			delete_file(name_im_mirr_flip)
			delete_file(name_im_flip)

	except Exception:
		print(Exception)
		delete_file(name_im)
		delete_file(name_im_mir)
		delete_file(name_im_mirr_flip)
		delete_file(name_im_flip)
		continue
	
	try:
		if expansion == "gif":
			name_im = image_url[image_url.rfind("/")+1:len(image_url)].lower()
			print(name_im)
			handle = open(name_im,"wb")
			handle.write(link['image_bytes'])
			handle.close()
			bag_hash = []
			mas_hash = []

			mas = processImage(name_im)
			for item in mas:
				mas_hash = images_hash(item)
				bag_hash.append(mas_hash)

			index = {'_id': image_url}
			result = { "$set": {'url_from_page': url, 'has_im': bag_hash, 'last_modified_in_db': mod}}
			db.images_with_hash.update_one(index, result, upsert = True)
			if db.images_with_hash.find({"_id": image_url}):
				print(image_url + " updated")

			idetif = {'_id': image_url}
			new_item = { "$set": {'url_from_page': url, 'image_bytes': image_bytes, "last_modified": mod}}
			db.images_hash_was_taken.update_one( idetif, new_item, upsert = True)
			db.content_images.delete_one(link)

			delete_file(name_im)
			for item in mas:
				delete_file(item)

		if (expansion != "gif") and (expansion != "png") and (expansion != "jpg") and (expansion != "jpeg"):
			continue
	except Exception:
		print(Exception)
		for item in mas:
				delete_file(item)
		continue 