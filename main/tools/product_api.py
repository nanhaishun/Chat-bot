import requests
import json
from flask import Flask, request, abort, Response, jsonify

def tulingChat(info = None): 
    api_url = 'http://172.23.16.10:58914/dlg-svc/service/data/v1/search'
    # api_url = 'http://172.23.16.10:58914/dlg-svc/service/data/v1/product'
    
    # api_url = 'http://172.28.61.250:50005/conversations/default/respond'
    data = {'keywords': info, 'pageIndex': 1, 'pageSize':5}
    # data = json.dumps({"partyNo":"111", "question":"hello","channel":"APP","appVersion":"3.7.3.1","msgId":"EDEDE12345678"})
    # data = {'id':'14201917'}
    # data = {'id':'78285164'}
    #data = {'userId':'2322','question':info}
    req = requests.post(api_url, data=data).text
    replies = json.loads(req)
    return replies


if __name__ == "__main__":
    res=tulingChat("尊理财")
    print(res)



