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
 
def Get_result(url):
    rs = requests.session()
    rs.proxies['http'] = os.getenv("proxy", "socks5h://localhost:9150")
    rs.proxies['https'] = os.getenv("proxy", "socks5h://localhost:9150")
    rs.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0'
    rs.headers['Accept-Language'] = 'Accept-Language: en-US,en;q=0.5'
    result = rs.get(url, timeout=1000)
    rs.close()
    return result

def get_header(image_url):
    r = Get_result(image_url)
    try:
        date = r.headers['Last-Modified']
    except Exception:
        date = r.headers['Date']
    finally:
        return date

# Удаление файла 
def delete_file(FileName):
    if os.path.exists(FileName):
        os.remove(FileName)
    else:
        print("The " + FileName + " does not exist")
    return None

def save_bytes(im_bytes):    
    handle = open(name_im,"wb")
    handle.write(im_bytes)
    handle.close()

def image_size(FileName):
    im = Image.open(FileName)
    result = im.size
    return result

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

for link in images_hash_was_taken.find():     
    try:
        image_url = link['_id']
        im_bytes = link['image_bytes']

        grip = 0
        date = "_"
        try:
            date = link['last_modified_in_db']
        except:
            # try:
            #     date = get_header(image_url)
            # except Exception:
            #     pass
            grip = 1

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

        if (expansion == "png") or (expansion == "jpg") or (expansion == "jpeg"):
            name_im = image_url[image_url.rfind("/")+1:len(image_url)].lower()

            handle = open(name_im,"wb")
            handle.write(link['image_bytes'])
            handle.close()

            image_proportions = image_size(name_im)

            index = {'_id': image_url}

            if grip == 1:
                result = { "$set": {'size': image_proportions, 'last_modified': datetime.datetime.utcnow()}}
            if grip == 0:
                result = { "$set": {'size': image_proportions, 'last_modified': date}}

            db.images_with_hash.update_one(index, result, upsert = True)
            if db.images_with_hash.find({"_id": image_url}):
                print(image_url + " updated")
                
            db.content_images.delete_one(link)
            delete_file(name_im)

        if expansion == "gif":
            name_im = image_url[image_url.rfind("/")+1:len(image_url)].lower()
            print(name_im)

            index = {'_id': image_url}
            result = { "$set": {'last_modified': date}}
            db.images_with_hash.update_one(index, result, upsert = True)

            if db.images_with_hash.find({"_id": image_url}):
                print(image_url + " updated")
    
    except Exception:
        print(Exception)
        continue