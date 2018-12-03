import time
import hashlib
import requests
import re

def get_response(msg):
    ##云智小钛 api
    # api = 'http://iask.qq.com/aics/open/ask?'
    api = 'http://172.22.64.67/dlg-gw/service/qq/iask?'
    SecretKey = 'cd68d8ebdff1ea4dc3d509d7a0e37044'
    appId ="&appId=2d65411e373a10e2d11b783899f0e667"
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
    msg=re.sub(r'[A-Za-z0-9]|/d+','',msg) #delet numbers and letters
    # if len(msg)==0:
    #     msg='hi'
    res=lambda msg:'hi' if len(msg)==0 else msg
    print(get_response(res(msg)))
