import requests
import json
from datetime import datetime,timedelta
def tulingChat(info = '你叫什么名字'):  
    api_url = 'http://www.tuling123.com/openapi/api'  
    apikey = 'e9a405a6ea8043d7bc628dbf0df77621'  
    data = {'key': apikey,  
                'info': info}  
    req = requests.post(api_url, data=data).text  
    replys = json.loads(req)['text']  
    return replys

if __name__ == "__main__":
    #res=tulingChat("今天股市不好，有什么建议")
    #print(res)
    print (datetime.now() + timedelta(seconds=30))