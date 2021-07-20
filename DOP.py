from pymongo import MongoClient 
from bson.objectid import ObjectId
import requests
import os
import time
import json
from bs4 import BeautifulSoup
import datetime

# установление соединения, получения url как объект
def Get_result(url):
	session = requests.session()
	session.proxies['http'] = os.getenv("proxy", "socks5h://localhost:9150")
	session.proxies['https'] = os.getenv("proxy", "socks5h://localhost:9150")
	session.proxies['User-Agent'] = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:71.0) Gecko/20100101 Firefox/71.0'
	session.headers['Accept-Language'] = 'Accept-Language: en-US,en;q=0.5'
	result = session.get(url, timeout=999)
	session.close()

	return result

# получение списка из ссылок с одного url 
def Get_hrefs(html):
	result = []
	soup = BeautifulSoup(html,'html')
	url_ahmia = ('https:')
	for tag in soup.find_all("cite"):
		value = tag.text
		if (value.find('.onion') == -1):
			continue
		result.append(value)
	#print(result)
	return result

# обработка ссылок 
def Link_processing(links):
	s_plus = 'http://'
	result = []
	for value in links:
		if value[-1] == '/':
			value = value[:-1]
		if value[-1] == '#':
			value = value[:-1]
		url = s_plus + value
		result.append(url)

	return result

#основная часть, достающая ссылки по запросу из файла
# подключение к бд
client = MongoClient()
db = client.dark_content
unsckanned_links = db.unsckanned_links

# работа с файлом
handle = open("Values_dop","r")
hrefs_from_html = []
url_from_line = []
url_ahmia = ('https://ahmia.fi/search/?q=')

# работа с получеными из файла ключевыми словами
for line in handle:
    print(line)
    line = line.rstrip()
    line_plus_url_ahmia = url_ahmia + line
    result = Get_result(line_plus_url_ahmia)
    result_html = (result.text)
    hrefs_from_html = Link_processing(Get_hrefs(result_html))
    i = 0

    for url in hrefs_from_html:
    	string = 'link_' + str(i)
    	index_text = {'_id': url}
    	new_one = { "$set": {"name": string, "last_modified": datetime.datetime.utcnow()}}
    	db.unsckanned_links.update_one( index_text, new_one, upsert = True)
    	#db.unsckanned_links.insert_one({"_id": url, "name": string, "last_modified": datetime.datetime.utcnow()})
    	i = i + 1
handle.close()