# -*- coding: UTF-8 -*-

import argparse
import logging
import warnings
import random
import pandas as pd
import difflib
import requests
import json
import hashlib
import time

from rasa_core.actions import Action
from rasa_core.actions.forms import FormAction
from rasa_core.agent import Agent
from rasa_core.channels.console import ConsoleInputChannel
from rasa_core.events import SlotSet,ReminderScheduled
from rasa_core.interpreter import RasaNLUInterpreter
from rasa_core.policies.keras_policy import KerasPolicy
from rasa_core.policies.memoization import MemoizationPolicy
from rasa_core.featurizers import (MaxHistoryTrackerFeaturizer,
                                   BinarySingleStateFeaturizer)
from rasa_core.channels import HttpInputChannel
from rasa_core.policies.fallback import FallbackPolicy

import warnings

#warnings.filterwarnings('ignore')

# logging.basicConfig(level=logging.DEBUG,  
#                     format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',  
#                     datefmt='%a, %d %b %Y %H:%M:%S',  
#                     filename='./test.log',  
#                     filemode='w')  

# logging.debug('debug message')  
logging.info('info message')  
# logging.warning('warning message')  
# logging.error('error message')  
# logging.critical('critical message') 

# logger = logging.getLogger(__name__)


PRODUCT_INTENTS = ['invest_scope','invest_return','invest_manager','invest_risk','invest_period','invest_amount','invest_time','invest_coupon']

OTHER_INTENTS = ['product_names']

def tuling_api(query):
    import json

    replys="我不理解你，请换个说法"
    
    api_url = 'http://www.tuling123.com/openapi/api'  
    apikey = 'e9a405a6ea8043d7bc628dbf0df77621' 
    info = query
    #print(info)
    data = {'key': apikey,  
                'info': info}  
    replys=''
    try: 
        req = requests.post(api_url, data=data).text  
        replys = json.loads(req)['text']
        replys = replys+ "\n" + json.loads(req)['url']
    except:
        return []
    return replys


def qq_api(id,msg):
    ##云智小钛 api
    api = 'http://iask.qq.com/aics/open/ask?'
    SecretKey = '1b762f5d584b8c4443a967beff6abf0e'
    appId ="&appId=53ff357543d12297d0c359de05eef942"
    #0:api/1:公众号/2:桌面网站/3:移动互联网
    channel ='&channel=0'
    
    uuId ='&uuId='+str(id)
    query = '&query='+str(msg)
    times ='&time='+str(round(time.time()))
    
    temp =appId+channel+query+times+uuId 
    temps = SecretKey+temp

    x = md5_api(temps)

    sign ='&sign='+x
    data = api+appId+uuId+channel+query+times+sign
    # print(data)
    r = requests.get(data)

    return r.json()['data']['answer']

#用于md5加密
def md5_api(temps):
    md = hashlib.md5()
    md.update(temps.encode())
    return md.hexdigest()

class ActionCleanSlot(Action):

    def name(self):
        return 'action_cleanslot'

    def run(self, dispatcher, tracker, domain):

        intent=tracker.latest_message.intent.get("name")
        if intent not in PRODUCT_INTENTS and intent not in OTHER_INTENTS:
            return [SlotSet("last_product_intent",None),SlotSet("product", None),SlotSet("last_product_name", None),SlotSet("last_product_information", None)]
        else:
            return []

def SearchProductName(info = None): 
    # api_url = 'http://172.23.16.24:80/dlg-svc/service/data/v1/search'
    api_url = 'http://172.23.16.10:58914/dlg-svc/service/data/v1/search'
    data = {'keywords': info, 'pageIndex': 1, 'pageSize':5}
    req = requests.post(api_url, data=data).text
    replies = json.loads(req)
    return replies

def GetProductInfo(productId = None): 
    # api_url = 'http://172.23.16.24:80/dlg-svc/service/data/v1/product'
    api_url = 'http://172.23.16.10:58914/dlg-svc/service/data/v1/product'
    data = {'id':productId}
    req = requests.post(api_url, data=data).text
    replies = json.loads(req)
    return replies

def GetXiaoanResponse(userId = None , info = None): 
    # api_url = 'http://172.23.16.24:80/dlg-svc/service/data/v1/xiaoan'
    api_url = 'http://172.23.16.10:58914/dlg-svc/service/data/v1/xiaoan'
    data = {'userId':userId,'question':info}
    req = requests.post(api_url, data=data).text
    replies = json.loads(req)
    # print(replies)
    return replies

"""       
class ActionSearchProduct(Action):

    def name(self):
        return 'action_searchproduct'

    def run(self, dispatcher, tracker, domain):

        product_intent=tracker.latest_message.intent.get("name")

        if product_intent == "product_names" or product_intent in PRODUCT_INTENTS:
            # print("last message: "+str(tracker.latest_message))
            # print("last message: "+tracker.latest_message.text)
            if len(tracker.latest_message.text)<=1:
                dispatcher.utter_template("utter_default",tracker)
                return []


        product_intent_confidence=tracker.latest_message.intent.get("confidence")

        print("product_intent: "+str(product_intent))
        last_product_intent = tracker.get_slot("last_product_intent")
        print("last_product_intent: "+str(last_product_intent))

        product_name=tracker.get_slot("product")
        if product_name is None:
            dispatcher.utter_message("您想查询什么产品？")
            if product_intent in PRODUCT_INTENTS:
                return [SlotSet("last_product_intent",product_intent)]
            else:
                return []
        print ("product: "+product_name)

        
        if product_intent_confidence>=0.9:
            pass
        elif product_intent_confidence>=0.6:
            # list_product_intent=tracker.latest_message.parse_data["intent_ranking"]
            # list_product_intent_names=[e.get("name") for e in list_product_intent if e.get("confidence")>=0.2]
            # dispatcher.utter_message("你想查询{%s}的什么信息呢？%s？"%(product_name,str(list_product_intent)))
            # dispatcher.utter_message("你想查询{%s}的什么信息呢？%s？"%(product_name,str(list_product_intent_names)))
            dispatcher.utter_message("你想查询{%s}的什么信息呢？\n[零钱理财,期限理财,网贷,基金,私募资管,保险,会员交易区]？"%product_name)
            return []
        else:
            if (product_intent not in PRODUCT_INTENTS) and (last_product_intent not in PRODUCT_INTENTS):
                # dispatcher.utter_message("你想查询{%s}的什么信息呢？[投资范围|收益率|管理人|风险|期限|金额|募集时间|优惠]？"%product_name)
                dispatcher.utter_message("你想查询{%s}的什么信息呢？\n[零钱理财,期限理财,网贷,基金,私募资管,保险,会员交易区]？"%product_name)
                return []


        product_information=tracker.get_slot("last_product_information")

        if product_information is not None:
            name_similarity=difflib.SequenceMatcher(None, product_name, product_information['DISPLAY_NAME'].lower()).quick_ratio()
            if name_similarity>0.9:
                if product_intent in PRODUCT_INTENTS:
                    self.output_of_intent(dispatcher,product_intent,product_information,tracker)
                    return [SlotSet("last_product_intent",product_intent)]
                elif last_product_intent in PRODUCT_INTENTS:
                    self.output_of_intent(dispatcher,last_product_intent,product_information,tracker)
                    return []                    


        df=pd.read_csv('./data/products_new.csv',header=0)
        
        list_products = [(e, difflib.SequenceMatcher(None, product_name, e.lower()).quick_ratio()) for e in list(df['DISPLAY_NAME'])] 
        list_products_sorted = sorted(list_products, key=lambda d: d[1], reverse=True)
        # print(list_products_sorted)
        count=0
        for e in list_products_sorted:
            if e[1]>0.9:
                l1=list(df.columns.values)
                l2=list(df[df['DISPLAY_NAME']==e[0]].iloc[0])
                d=dict()
                for i in range(len(l1)):
                    d[l1[i]]=l2[i]
                # print(d)
                # print(dict(zip((l1,l2))))
                if product_intent in PRODUCT_INTENTS:
                    self.output_of_intent(dispatcher,product_intent,d,tracker)
                    return [SlotSet("last_product_intent",product_intent),SlotSet("last_product_information", d)]
                elif last_product_intent in PRODUCT_INTENTS:
                    self.output_of_intent(dispatcher,last_product_intent,d,tracker)
                    return [SlotSet("last_product_information", d)]  
                else:
                    dispatcher.utter_message("你想查询{%s}的什么信息呢？\n[投资范围|收益率|管理人|风险|期限|金额|募集时间|优惠]？"%product_name)
                    return [SlotSet("last_product_information", d)]                      
            elif e[1]>0.5:
                if count==0:
                    dispatcher.utter_message("您查询{%s}的相似产品如下："%product_name)
                count+=1
                dispatcher.utter_message("(%s). {%s}?"%(count,e[0]))
                if count>=5:
                    if product_intent in PRODUCT_INTENTS:
                        return [SlotSet("last_product_intent",product_intent)]
                    else:
                        return []
            else:
                if count>0:
                    if product_intent in PRODUCT_INTENTS:
                        return [SlotSet("last_product_intent",product_intent)]
                    else:
                        return []
                dispatcher.utter_message("数据库没有找到你要查的{%s}产品，还有什么可以帮您的？"%product_name)
                if product_intent in PRODUCT_INTENTS:
                    return [SlotSet("last_product_intent",product_intent)]
                else:
                    return []
        
        # dispatcher.utter_message("你想查询{%s}的什么信息呢？[投资范围|收益率|管理人|风险|期限|金额|募集时间|优惠]？"%product_name)
        return []

    def output_of_intent(self,dispatcher,product_intent,product_information,tracker):
        if product_intent=='invest_scope' : #'投资范围':
            dispatcher.utter_message("该{%s}主要投资范围包含：（%s）,为投资者提供长期稳定的回报。近期业绩收益高达（%s）"%(product_information['DISPLAY_NAME'],product_information['INVEST_SCOPE'],product_information['INTEREST_RATE_DISPLAY']))
        elif product_intent=='invest_return': #'收益率':
            dispatcher.utter_message("{%s}近期的业绩收益高达（%s），同期的最大回撤为（null），同期沪深300/上证综指的涨/跌幅为（null）（插入历史比较收益曲线）"%(product_information['DISPLAY_NAME'],product_information['INTEREST_RATE_DISPLAY']))
        elif product_intent=='invest_manager': #'管理人':
            dispatcher.utter_message("该{%s}的管理人是（%s），基金管理人是（null）"%(product_information['DISPLAY_NAME'],product_information['FUND_MANAGER_NAME']))
        elif product_intent=='invest_risk': #'风险':
            dispatcher.utter_message("目前所有产品都不能承诺保本保收益，{%s}的风险等级是（%s），存在本金亏损的风险"%(product_information['DISPLAY_NAME'],product_information['RISK_LEVEL']))
        elif product_intent=='invest_period': #'期限':
            dispatcher.utter_message("{%s}的投资期限为（%s）。其中封闭期为（null）。（赎回规则）"%(product_information['DISPLAY_NAME'],product_information['PERIOD']))
        elif product_intent=='invest_amount' : #'金额':
            dispatcher.utter_message("该{%s}的起投金额为（%s），追加金额是（%s）"%(product_information['DISPLAY_NAME'],product_information['MIN_INVEST_AMOUNT'],product_information['INCREASE_INVEST_AMOUNT']))
        elif product_intent=='invest_time': #'募集时间':
            dispatcher.utter_message("该{%s}销售时间为（%s）；预约时间为（null），预约金额为（null），预览时间为（null）"%(product_information['DISPLAY_NAME'],product_information['OPENING_DATE']))
        elif product_intent=='invest_coupon': #'优惠':
            dispatcher.utter_message("{%s}申购费为（%s）；（不可以）使用投资券；该{%s}（有）折扣,折扣为（%s）；"%(product_information['DISPLAY_NAME'],product_information['BUY_FEE_DISCOUNT_DESC'],product_information['DISPLAY_NAME'],product_information['REDEMPTION_FEE_RATE_DESC']))
        else:
            dispatcher.utter_template("utter_default")
"""

class ActionSearchProduct(Action):

    def name(self):
        return 'action_searchproduct'

    def run(self, dispatcher, tracker, domain):

        product_intent=tracker.latest_message.intent.get("name")

        if product_intent == "product_names" or product_intent in PRODUCT_INTENTS:
            # print("last message: "+str(tracker.latest_message))
            # print("last message: "+tracker.latest_message.text)
            if len(tracker.latest_message.text)<=1:
                dispatcher.utter_template("utter_default",tracker)
                return []


        product_intent_confidence=tracker.latest_message.intent.get("confidence")

        print("product_intent: "+str(product_intent))
        last_product_intent = tracker.get_slot("last_product_intent")
        print("last_product_intent: "+str(last_product_intent))

        product_name=tracker.get_slot("product")
        if product_name is None:
            dispatcher.utter_message("您想查询什么产品？")
            if product_intent in PRODUCT_INTENTS:
                return [SlotSet("last_product_intent",product_intent)]
            else:
                return []
        print ("product: "+product_name)


        last_product_name=tracker.get_slot("last_product_name")
        print("last_product_name: "+str(last_product_name))

        if last_product_name != product_name:

        else:
            product_information=tracker.get_slot("last_product_information")
            # print("last_product_name:"+last_product_name+" product_name:"+product_name)
            if product_information is None:
                products_information=SearchProductName(product_name)
                if len(products_information['data'])==0:
                    dispatcher.utter_message("数据库没有找到你要查的{%s}产品，还有什么可以帮您的？"%product_name)
                    if product_intent in PRODUCT_INTENTS:
                        return [SlotSet("last_product_intent",product_intent),SlotSet("last_product_name",product_name)]
                    else:
                        return [SlotSet("last_product_name",product_name)]

                products_names = [(e['displayName'],e['id']) for e in products_information['data']]
                list_products = [(e, difflib.SequenceMatcher(None, product_name.replace(' ','').lower(), e.replace(' ','').lower()).quick_ratio(),ids) for (e,ids) in  products_names]
                list_products_sorted = sorted(list_products, key=lambda d: d[1], reverse=True)

                count=0
                tmp_msg=[]

                for e in list_products_sorted:
                    if e[1]>0.8:
                        res = GetProductInfo(e[2])
                        if len(res['data'])==0:
                            dispatcher.utter_message("数据库没有找到你要查的{%s}产品，还有什么可以帮您的？"%product_name)
                            if product_intent in PRODUCT_INTENTS:
                                return [SlotSet("last_product_intent",product_intent),SlotSet("last_product_name",product_name)]
                            else:
                                return [SlotSet("last_product_name",product_name)]                            

                        if product_intent in PRODUCT_INTENTS:
                            self.output_of_intent(dispatcher,product_intent,res['data'],tracker,domain)
                            # print("2222 product_intent:"+product_intent)
                            return [SlotSet("last_product_intent",product_intent),SlotSet("last_product_information", res['data']),SlotSet("last_product_name",product_name)]
                        elif last_product_intent in PRODUCT_INTENTS:
                            self.output_of_intent(dispatcher,last_product_intent,res['data'],tracker,domain)
                            # print("3333 product_intent:"+product_intent)
                            return [SlotSet("last_product_information", res['data']),SlotSet("last_product_name",product_name)]  
                        else:
                            # print("4444 product_intent:"+product_intent)
                            dispatcher.utter_message("你想查询{%s}的什么信息呢？\n[投资范围|收益率|管理人|风险|期限|金额|募集时间|优惠]"%product_name)
                            return [SlotSet("last_product_information", res['data']),SlotSet("last_product_name",product_name)]
                    elif e[1]>0.5:
                        # if count==0:
                        #     dispatcher.utter_message("您查询{%s}的相似产品如下："%product_name)
                        count+=1
                        # dispatcher.utter_message("(%s). {%s}?"%(count,e[0]))
                        tmp_msg.append({"content":"%s"%(e[0]),"reply":"%s"%(e[0]),"echoReply":"Y"})
                        if count==5 or count==len(list_products_sorted):
                            msg=dict({"content":"您查询{%s}的相似产品如下："%product_name})
                            msg2=dict({"link":str(tmp_msg)})
                            msg=str(dict(msg,**msg2)).replace('\n','')
                            # print("msg:"+msg) 
                            dispatcher.utter_message(msg)
                            if product_intent in PRODUCT_INTENTS:
                                return [SlotSet("last_product_intent",product_intent),SlotSet("last_product_name",product_name)]
                            else:
                                return [SlotSet("last_product_name",product_name)]
                    else:
                        if count>0:
                            msg=dict({"content":"您查询{%s}的相似产品如下："%product_name})
                            msg2=dict({"link":str(tmp_msg)})
                            msg=str(dict(msg,**msg2)).replace('\n','')                            
                            dispatcher.utter_message(msg)
                            if product_intent in PRODUCT_INTENTS:
                                return [SlotSet("last_product_intent",product_intent),SlotSet("last_product_name",product_name)]
                            elif last_product_intent in PRODUCT_INTENTS:
                                return [SlotSet("last_product_name",product_name)]                              
                            else:
                                return [SlotSet("last_product_name",product_name)]
                        dispatcher.utter_message("数据库没有找到你要查的{%s}产品，还有什么可以帮您的？"%product_name)
                        if product_intent in PRODUCT_INTENTS:
                            return [SlotSet("last_product_intent",product_intent),SlotSet("last_product_name",product_name)]
                        else:
                            return [SlotSet("last_product_name",product_name)]

            else:
                if product_intent in PRODUCT_INTENTS:
                    self.output_of_intent(dispatcher,product_intent,product_information,tracker,domain)
                    return [SlotSet("last_product_intent",product_intent),SlotSet("last_product_name",product_name)]
                elif last_product_intent in PRODUCT_INTENTS:
                    self.output_of_intent(dispatcher,last_product_intent,product_information,tracker,domain)
                    return [SlotSet("last_product_name",product_name)]  
                else:
                    dispatcher.utter_message("你想查询{%s}的什么信息呢？\n[投资范围|收益率|管理人|风险|期限|金额|募集时间|优惠]"%product_name)
                    return [SlotSet("last_product_information",product_information),SlotSet("last_product_name",product_name)]            
        
        # dispatcher.utter_message("你想查询{%s}的什么信息呢？[投资范围|收益率|管理人|风险|期限|金额|募集时间|优惠]"%product_name)
        # return [SlotSet("last_product_name",product_name)]


    def search_product_info (self,dispatcher,tracker,domain,product_intent,last_product_intent,product_name,last_product_name,last_product_information):

                products_information=SearchProductName(product_name)
                if len(products_information['data'])==0:
                    dispatcher.utter_message("数据库没有找到你要查的{%s}产品，还有什么可以帮您的？"%product_name)
                    if product_intent in PRODUCT_INTENTS:
                        return [{"last_product_intent",product_intent,"last_product_name",product_name}]
                    else:
                        return [SlotSet("last_product_name",product_name)]

                products_names = [(e['displayName'],e['id']) for e in products_information['data']]
                list_products = [(e, difflib.SequenceMatcher(None, product_name.replace(' ','').lower(), e.replace(' ','').lower()).quick_ratio(),ids) for (e,ids) in  products_names]
                list_products_sorted = sorted(list_products, key=lambda d: d[1], reverse=True)

                count=0
                tmp_msg=[]

                for e in list_products_sorted:
                    if e[1]>0.8:
                        res = GetProductInfo(e[2])
                        if len(res['data'])==0:
                            dispatcher.utter_message("数据库没有找到你要查的{%s}产品，还有什么可以帮您的？"%product_name)
                            if product_intent in PRODUCT_INTENTS:
                                return [SlotSet("last_product_intent",product_intent),SlotSet("last_product_name",product_name)]
                            else:
                                return [SlotSet("last_product_name",product_name)]                            

                        if product_intent in PRODUCT_INTENTS:
                            self.output_of_intent(dispatcher,product_intent,res['data'],tracker,domain)
                            # print("2222 product_intent:"+product_intent)
                            return [SlotSet("last_product_intent",product_intent),SlotSet("last_product_information", res['data']),SlotSet("last_product_name",product_name)]
                        elif last_product_intent in PRODUCT_INTENTS:
                            self.output_of_intent(dispatcher,last_product_intent,res['data'],tracker,domain)
                            # print("3333 product_intent:"+product_intent)
                            return [SlotSet("last_product_information", res['data']),SlotSet("last_product_name",product_name)]  
                        else:
                            # print("4444 product_intent:"+product_intent)
                            dispatcher.utter_message("你想查询{%s}的什么信息呢？\n[投资范围|收益率|管理人|风险|期限|金额|募集时间|优惠]"%product_name)
                            return [SlotSet("last_product_information", res['data']),SlotSet("last_product_name",product_name)]
                    elif e[1]>0.5:
                        # if count==0:
                        #     dispatcher.utter_message("您查询{%s}的相似产品如下："%product_name)
                        count+=1
                        # dispatcher.utter_message("(%s). {%s}?"%(count,e[0]))
                        tmp_msg.append({"content":"%s"%(e[0]),"reply":"%s"%(e[0]),"echoReply":"Y"})
                        if count==5 or count==len(list_products_sorted):
                            msg=dict({"content":"您查询{%s}的相似产品如下："%product_name})
                            msg2=dict({"link":str(tmp_msg)})
                            msg=str(dict(msg,**msg2)).replace('\n','')
                            # print("msg:"+msg) 
                            dispatcher.utter_message(msg)
                            if product_intent in PRODUCT_INTENTS:
                                return [SlotSet("last_product_intent",product_intent),SlotSet("last_product_name",product_name)]
                            else:
                                return [SlotSet("last_product_name",product_name)]
                    else:
                        if count>0:
                            msg=dict({"content":"您查询{%s}的相似产品如下："%product_name})
                            msg2=dict({"link":str(tmp_msg)})
                            msg=str(dict(msg,**msg2)).replace('\n','')                            
                            dispatcher.utter_message(msg)
                            if product_intent in PRODUCT_INTENTS:
                                return [SlotSet("last_product_intent",product_intent),SlotSet("last_product_name",product_name)]
                            elif last_product_intent in PRODUCT_INTENTS:
                                return [SlotSet("last_product_name",product_name)]                              
                            else:
                                return [SlotSet("last_product_name",product_name)]
                        dispatcher.utter_message("数据库没有找到你要查的{%s}产品，还有什么可以帮您的？"%product_name)
                        if product_intent in PRODUCT_INTENTS:
                            return [SlotSet("last_product_intent",product_intent),SlotSet("last_product_name",product_name)]
                        else:
                            return [SlotSet("last_product_name",product_name)]


    def output_of_intent(self,dispatcher,product_intent,product_information,tracker,domain):
        try:
            if product_intent=='invest_scope' : #'投资范围':
                msg=dict({"content":"该{%s}主要投资范围包含基金和债券,为投资者提供长期稳定的回报。近期业绩收益高达（%s）"%(product_information['displayName'],product_information['interestRateDisplay'])})
                tmp_msg=str([{"content":"我要投资{%s}"%product_information['displayName'],"url":"lufax://financedetail?productid=%s"%product_information['id']}])
                msg2=dict({"link":tmp_msg})
                msg=str(dict(msg,**msg2)).replace('\n','')
                dispatcher.utter_message(msg)
            elif product_intent=='invest_return': #'收益率':
                msg=dict({"content":"{%s}近期的业绩收益高达（%s），同期的最大回撤为(0.03)，同期沪深300/上证综指的涨/跌幅为（0.06）"%(product_information['displayName'],product_information['interestRateDisplay'])})
                tmp_msg=str([{"content":"我要投资{%s}"%product_information['displayName'],"url":"lufax://financedetail?productid=%s"%product_information['id']}])
                msg2=dict({"link":tmp_msg})
                msg=str(dict(msg,**msg2)).replace('\n','')
                dispatcher.utter_message(msg)
            elif product_intent=='invest_manager': #'管理人':
                msg=dict({"content":"该{%s}的管理人是（平安资管），基金管理人是（王晓歌）"%(product_information['displayName'])})
                tmp_msg=str([{"content":"我要投资{%s}"%product_information['displayName'],"url":"lufax://financedetail?productid=%s"%product_information['id']}])
                msg2=dict({"link":tmp_msg})
                msg=str(dict(msg,**msg2)).replace('\n','')
                dispatcher.utter_message(msg)
            elif product_intent=='invest_risk': #'风险':
                msg=dict({"content":"目前所有产品都不能承诺保本保收益，{%s}的风险等级是（%s）星，存在本金亏损的风险"%(product_information['displayName'],product_information['riskLevel'])})
                tmp_msg=str([{"content":"我要投资{%s}"%product_information['displayName'],"url":"lufax://financedetail?productid=%s"%product_information['id']}])
                msg2=dict({"link":tmp_msg})
                msg=str(dict(msg,**msg2)).replace('\n','')
                dispatcher.utter_message(msg)
            elif product_intent=='invest_period': #'期限':
                msg=dict({"content":"{%s}的投资期限为（%s）。其中封闭期为（30天）。（赎回规则）"%(product_information['displayName'],product_information['investPeriod'])})
                tmp_msg=str([{"content":"我要投资{%s}"%product_information['displayName'],"url":"lufax://financedetail?productid=%s"%product_information['id']}])
                msg2=dict({"link":tmp_msg})
                msg=str(dict(msg,**msg2)).replace('\n','')
                dispatcher.utter_message(msg)
            elif product_intent=='invest_amount' : #'金额':
                msg=dict({"content":"该{%s}的起投金额为（%s），追加金额是（%s）"%(product_information['displayName'],product_information['minInvestAmount'],product_information['increaseInvestAmount'])})
                tmp_msg=str([{"content":"我要投资{%s}"%product_information['displayName'],"url":"lufax://financedetail?productid=%s"%product_information['id']}])
                msg2=dict({"link":tmp_msg})
                msg=str(dict(msg,**msg2)).replace('\n','')
                dispatcher.utter_message(msg)
            elif product_intent=='invest_time': #'募集时间':
                msg=dict({"content":"该{%s}销售时间为（%s）；结束时间为（%s）"%(product_information['displayName'],product_information['publishedAt'],product_information['trxEndAt'])})
                tmp_msg=str([{"content":"我要投资{%s}"%product_information['displayName'],"url":"lufax://financedetail?productid=%s"%product_information['id']}])
                msg2=dict({"link":tmp_msg})
                msg=str(dict(msg,**msg2)).replace('\n','')
                dispatcher.utter_message(msg)
            elif product_intent=='invest_coupon': #'优惠':
                msg=dict({"content":"{%s}申购费为（0.03）；（不可以）使用投资券；该{%s}（有）折扣,折扣为（0.8）；"%(product_information['displayName'],product_information['displayName'])})
                tmp_msg=str([{"content":"我要投资{%s}"%product_information['displayName'],"url":"lufax://financedetail?productid=%s"%product_information['id']}])
                msg2=dict({"link":tmp_msg})
                msg=str(dict(msg,**msg2)).replace('\n','')
                dispatcher.utter_message(msg)
            else:
                dispatcher.utter_template("utter_default",tracker)
        except:
            dispatcher.utter_message("{'content':'此{%s}的该类别信息没有找到，请尝试其他的','link':'[]'}" %product_information['displayName'])



class ActionTuling(Action): 

    def name(self):
        return 'action_tuling'

    def run(self, dispatcher, tracker, domain):
        query=tracker.latest_message.text
        try:
            dispatcher.utter_message(qq_api(tracker.sender_id,query))
        except:
            dispatcher.utter_template("utter_default",tracker)        
        return []      

class ActionXiaoan(Action): 

    def name(self):
        return 'action_xiaoan'

    def run(self, dispatcher, tracker, domain):
        query=tracker.latest_message.text
        print('tracker.sender_id: '+str(tracker.sender_id))
        try:
            dispatcher.utter_message(str(GetXiaoanResponse(tracker.sender_id,query)))
        except:
            dispatcher.utter_template("utter_default",tracker)
        return [] 

