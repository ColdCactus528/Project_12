import cv2
import difflib
from PIL import Image

# Переименование с добавлением res
def image_comprassion(FileName):
    len(FileName)
    entry_1 = FileName.find(".jpg")
    if entry_1 != -1:
        new_filename = FileName[:entry_1] + ("_res.jpg")
    if entry_1 == -1:
        entry_2 = FileName.find(".png")
        if entry_2 != -1:
            new_filename = FileName[:entry_2] + ("_res.png")
    return new_filename

# Сжатие изображения и сохранение под новым именем 
def resize_pic_8_8(FileName):
    pic = Image.open(FileName)
    print(pic.size)
    resized = pic.resize((8,8), Image.ANTIALIAS)
    new_name = image_comprassion(FileName)
    resized.save(new_name)
    return new_name

# Вычисления хэша
def CalcImageHash(FileName):
    res_image = resize_pic_8_8(FileName)
    image = cv2.imread(res_image)
    g_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    avg = g_image.mean() #Среднее значение пикселя
    ret, threshold_image = cv2.threshold(g_image, avg, 255, 0) #Бинаризация по порогу
    
    # Рассчет хэша
    _hash = ""
    for x in range(8):
        for y in range(8):
            val = threshold_image[x,y]
            if val == 255:
                _hash = _hash+"1"
            else:
                _hash = _hash+"0"
            
    return _hash
    
# Сравнение хэша
def CompareHash(hash1,hash2):
    l = len(hash1)
    i = 0
    count = 0
    while i<l:
        if hash1[i] != hash2[i]:
            count = count+1
        i = i+1
    return count
        
#file_1 = input()
#file_2 = input()
hash1 = CalcImageHash("Not_1.jpg")
hash2 = CalcImageHash("Not.jpg")
print(hash1)
print(hash2)
print(CompareHash(hash1, hash2))