import time
import hashlib
import requests

def get_response(msg):
    ##云智小钛 api
    api = 'http://iask.qq.com/aics/open/ask?'
    SecretKey = '1b762f5d584b8c4443a967beff6abf0e'
    appId ="&appId=53ff357543d12297d0c359de05eef942"
    #0:api/1:公众号/2:桌面网站/3:移动互联网
    channel ='&channel=0'
    
    uuId ='&uuId=1'
    query = '&query='+str(msg)
    times ='&time='+str(round(time.time()))
    
    temp =appId+channel+query+times+uuId 
    temps = SecretKey+temp

    x = md5_api(temps)
  
    sign ='&sign='+x
    data = api+appId+uuId+channel+query+times+sign
    print(data)
    r = requests.get(data)

    return r.json()['data']['answer']

#用于md5加密
def md5_api(temps):
    md = hashlib.md5()
    md.update(temps.encode())
    return md.hexdigest()


while True:
    msg = input()
    print(get_response(msg))
