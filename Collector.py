from pymongo import MongoClient 
import requests
import os
import time
import json
from bs4 import BeautifulSoup
import datetime 

# установление соединения, получения url как объект
def Get_result(url):
    rs = requests.session()
    rs.proxies['http'] = os.getenv("proxy", "socks5h://localhost:9150")
    rs.proxies['https'] = os.getenv("proxy", "socks5h://localhost:9150")
    rs.headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 6.1; rv:60.0) Gecko/20100101 Firefox/60.0'
    rs.headers['Accept-Language'] = 'Accept-Language: en-US,en;q=0.5'
    result = rs.get(url, timeout=1000)
    rs.close()
    return result

def Download_url(url):
    result = Get_result(url)
    return result.text

def Download_content(url):
    result = Get_result(url)
    return result.content

# получение картинок 
def Get_urls_to_images_from_page(html):
    result = []
    soap = BeautifulSoup(html)
    for img in soap.find_all('img'):
        img_url = img.get('src')
        img_url_str = str(img_url)
        if len(img_url_str) < 1:
            continue
        find = False
        for i in result:
            if i == img_url_str:
                find = True
                break
        if not find:
            result.append(img_url_str)
    return result

# получение текста
def Get_text(html):
	result = []
	soup = BeautifulSoup(html,'html')
	for tag in soup.find_all("p"):
		text = tag.text
		result.append(text)	

	return result

# правка ссылок на изображение 
def Fix_urls_by_site(urls, url_to_site):
    result = []
    if url_to_site[-1] == '/':
        url_to_site = url_to_site[:-1]
    for item in urls:
        if len(item) < 1:
            continue
        if item[0] == '/':
            item = url_to_site + item
        if item[:4] != "http":
            item = url_to_site + "/" + item
        find = False
        for i in result:
            if i == item:
                find = True
                break
        if not find:
            result.append(item)
    return result

def url_is_connected(url):
    i = 0
    while i < 3:
        try:
            result = get_result(url)
        except:
            i = i + 1
    return False

def get_header(image_url):
    r = Get_result(image_url)
    try:
        date = r.headers['Last-Modified']
        return date
    except Exception:
        date = r.headers['Date']
        return date

# проверка ссылок на изображение и запись или обновелние информации о них в бд
def Image_url_iteration(image_url, url):
    try:
        image_text = Download_url(image_url)
    except Exception:
        client = MongoClient()
        db = client.dark_content
        links_that_no_access = db.links_that_no_access
        identifier = {'_id': image_url}
        body = {"$set": {'last_modified': datetime.datetime.utcnow()}}
        db.links_that_no_access.update_one(identifier, body, upsert = True)
        if db.content_images.find({"_id": image_url}):
            print(image_url + " no access updated")
            
        return
    else:
        if "404" in image_text:
            return
        if "DOCTYPE html PUBLIC" in image_text:
            return
        image_bytes = Download_content(image_url)
        date = get_header(image_url)
        client = MongoClient()
        db = client.dark_content
        content_images = db.content_images
        index = {'_id': image_url}
        result = { "$set": {'url_from_page': url, 'image_bytes': image_bytes, "date_from_site": date , "last_modified": datetime.datetime.utcnow()}}
        db.content_images.update_one(index, result, upsert = True)
        if db.content_images.find({"_id": image_url}):
            print(image_url + " updated")
   
# получение text и content из бд 
client = MongoClient()
db = client.dark_content
sckanned_links = db.sckanned_links
content_texts = db.content_texts
content_images = db.content_images
skan_links = db.skan_url_to_url_to_images

for link in db.sckanned_links.find():
    html = link['html']
    url = link['_id']
    mod = link['last_modified']
    result_text = Get_text(html)
    result_images = Fix_urls_by_site(Get_urls_to_images_from_page(html),url)

    for result_image in result_images:
        try:
            Image_url_iteration(result_image, url)
        except:
            continue 
        finally:
            print(result_image + " " + "done")

# запись в бд с привязкой по url
    index_text = {'_id': url + "_text" }
    new_one = { "$set": {'text': result_text, "last_modified": datetime.datetime.utcnow()}}
    db.content_texts.update_one( index_text, new_one, upsert = True)
    idetif = {'_id': url}
    new_item = { "$set": {"html": html, "last_modified": mod}}
    db.skan_url_to_url_to_images.update_one( idetif, new_item, upsert = True)
    db.sckanned_links.delete_one(link)
