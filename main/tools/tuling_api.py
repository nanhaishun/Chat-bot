import requests

def tulingChat(question):
    KEY = 'e9a405a6ea8043d7bc628dbf0df77621'  # change to your API KEY
    url = 'http://www.tuling123.com/openapi/api'
    req_info = question.encode('utf-8')

    query = {'key': KEY, 'info': req_info}
    headers = {'Content-type': 'text/html', 'charset': 'utf-8'}

    try:
        # 方法一、用requests模块已get方式获取内容
        print(url+str(query))
        r = requests.get(url, params=query, headers=headers)
        res = r.text
        #req = requests.post(api_url, data=query).text
        print(req)
        #res = r.text
        result = json.loads(res).get('text').replace('<br>', '\n')
        #result = json.loads(req)['text'] 
    except:
        result="我不理解你，换个说法好吗？"

    return result

if __name__ == "__main__":
    res=tulingChat("我有88万块钱需要投资一年半时间")
    print(res)
