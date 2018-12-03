# -*- coding: UTF-8 -*-
import re
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

from rasa_core.configs.read_config import read_api_config
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

# warnings.filterwarnings('ignore')

# logging.basicConfig(level=logging.info,  
#                     format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',  
#                     datefmt='%a, %d %b %Y %H:%M:%S',  
#                     filename='./test.log',  
#                     filemode='w')  

# logging.debug('debug message')  
# logging.info('info message')
logger = logging.getLogger(__name__)
# logging.warning('warning message')  
# logging.error('error message')  
# logging.critical('critical message') 



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
    API_CONF = read_api_config()
    ##云智小钛 api
    # api = 'http://iask.qq.com/aics/open/ask?'
    api = 'http://'+API_CONF['host_qq']+'/dlg-gw/service/qq/iask?'
    SecretKey = 'cd68d8ebdff1ea4dc3d509d7a0e37044'
    appId ="&appId=2d65411e373a10e2d11b783899f0e667"
    #0:api/1:公众号/2:桌面网站/3:移动互联网
    channel ='&channel=0'
    
    uuId ='&uuId='+str(id)
    msg=re.sub(r'[A-Za-z0-9]|/d+','',msg) #delet numbers and letters
    f=lambda msg:'hi' if len(msg)==0 else msg
    query = '&query='+f(msg)
    times ='&time='+str(round(time.time()))
    
    temp =appId+channel+query+times+uuId 
    temps = SecretKey+temp

    x = md5_api(temps)
    
    sign ='&sign='+x
    data = api+appId+uuId+channel+query+times+sign
    # print(data)
    r = requests.get(data)
    # print(r.json())
    return r.json()['data']['answer']

#用于md5加密
def md5_api(temps):
    md = hashlib.md5()
    md.update(temps.encode())
    return md.hexdigest()

def SearchProductName(keywords = None,field=None,pageIndex=1,pageSize=5): 
    API_CONF = read_api_config()

    api_url = 'http://'+API_CONF['host_search']+'/dlg-data-app/service/data/v1/search'   
    # data = {'keywords': info, 'pageIndex': 1, 'pageSize':5, 'field':"['displayName','id','interestRateDisplay','productCategory','riskLevel','investPeriodInDays','minInvestAmount','fundManager','openingDate','lastCollectionDate','maxInterestRate','minInterestRate','buyFeeDiscount','subFeeDiscount','buyFeeRate','groupCode','buyStatus','productStatus','score','interestRate','investPeriod']"}
    if field is None:
        data = {'keywords': keywords, 'pageIndex': pageIndex, 'pageSize':pageSize}
    else:
        data = {'keywords': keywords, 'field':field ,'pageIndex': pageIndex, 'pageSize':pageSize}
    req = requests.post(api_url, data=data).text
    replies = json.loads(req)
    return replies

def GetProductInfo(productId = None): 
    API_CONF = read_api_config()

    api_url = 'http://'+API_CONF['host_product']+'/dlg-data-app/service/data/v1/product'
    data = {'id':productId}
    req = requests.post(api_url, data=data).text
    replies = json.loads(req)
    return replies

def GetXiaoanResponse(userId = None , info = None): 
    api_url = 'http://172.23.16.10:58914/dlg-svc/service/data/v1/xiaoan'
    data = {'userId':userId,'question':info}
    req = requests.post(api_url, data=data).text
    replies = json.loads(req)
    # print(replies)
    return replies

def output_text_convert(input):
    res  =list()
    res.append(str(input))
    return str(res)


class ActionTuling(Action): 

    def name(self):
        return 'action_tuling'

    def run(self, dispatcher, tracker, domain):
        from rasa_core.events import UserUtteranceReverted

        query=tracker.latest_message.text
        try:
            dispatcher.utter_message(output_text_convert(qq_api(tracker.sender_id,query)))
        except Exception as e:
            logger.exception("Caught a qq exception.")
            dispatcher.utter_template("utter_statements",tracker)        
        # return []
        return [UserUtteranceReverted()]      

class ActionXiaoan(Action): 

    def name(self):
        return 'action_xiaoan'

    def run(self, dispatcher, tracker, domain):
        query=tracker.latest_message.text
        # print('tracker.sender_id: '+str(tracker.sender_id))
        # print("{'XIAOAN':'%s')}"%query)
        dispatcher.utter_message("{'XIAOAN':'%s'}"%query)
        # dispatcher.utter_message(str(GetXiaoanResponse(tracker.sender_id,query)))
        return [] 

class ActionToPerson(Action): 

    def name(self):
        return 'action_to_person'

    def run(self, dispatcher, tracker, domain):
        dispatcher.utter_message("{'TO_PERSON':'TO_PERSON'}")
        return [] 

class ActionCleanSlot(Action):

    def name(self):
        return 'action_cleanslot'

    def run(self, dispatcher, tracker, domain):
        return [SlotSet("last_product_intent",None),SlotSet("product", None),SlotSet("last_product_name", None),SlotSet("last_product_information", None)]


class ActionRecProduct(Action):

    def name(self):
        return 'action_recproduct'

    def run(self, dispatcher, tracker, domain):
        pattern1 = re.compile('[风险|保本|稳定]')
        # pattern2 = re.compile('[少|低|小]')
        # pattern3 = re.compile('[大|多|高]')

        result1 = pattern1.findall(tracker.latest_message.text)
        # result2 = pattern2.findall(tracker.latest_message.text)
        # result3 = pattern3.findall(tracker.latest_message.text)

        choice_risk=tracker.get_slot("choice_risk")
        if len(result1)>0:
            choice_risk='低'


        # product = next(tracker.get_latest_entity_values("product"), None)
        # product_name= tracker.get_slot("product")
        product= tracker.get_slot("product")
        choice_product= tracker.get_slot("choice_product")

        # amount = next(tracker.get_latest_entity_values("amount"), None)
        # amount_name= tracker.get_slot("amount")
        amount = tracker.get_slot("amount")
        choice_amount= tracker.get_slot("choice_amount")

        print('product: '+str(product))
        print('amount: '+str(amount))
        print('choice_risk: '+str(choice_risk))

        interest_display = lambda x:x if x != 'None' else '浮动收益'
        if choice_product is not None :
            try:
                products_information=SearchProductName(keywords = choice_product,field="['displayName','id','interestRateDisplay','productCategory','groupCode','investPeriodInDays','minInvestAmount','openingDate','lastCollectionDate','riskLevel','productStatus']")
            except Exception as e:
                logger.exception("Caught a search product exception.")
                products_information={'data':[]}

            if len(products_information['data'])==0:
                dispatcher.utter_message(output_text_convert("数据库没有找到{%s}，还有什么可以帮您的？"%product))
                return [SlotSet("choice_risk", choice_risk)]

            # print(products_information['data']) 

            products_names = [(e['displayName'],e['id'],interest_display(e['interestRateDisplay']),e['minInvestAmount'],e['riskLevel'],e['investPeriodInDays'],e['productCategory'],e['groupCode']) for e in products_information['data']] 

            msg=str({"LucyID":"123","title":"给您推荐以下产品","cardList":[{'title':e[0],'leftValue':e[2],'leftKey':'起投%s元'%e[3],'rightValue':'风险%s星'%e[4],'rightKey':'期限%s天'%e[5],'note':'','schema':'lufax://financedetail?productid=%s'%e[1]} for e in products_names]})
            dispatcher.utter_message(str({'REC':msg}))
            return [SlotSet("choice_risk", None),SlotSet("choice_product", None),SlotSet("choice_amount", None),SlotSet("product", None),SlotSet("amount", None)]

        elif product is not None:
            try:
                products_information=SearchProductName(keywords = product,field="['displayName','id','interestRateDisplay','productCategory','groupCode','investPeriodInDays','minInvestAmount','openingDate','lastCollectionDate','riskLevel','productStatus','tag']")
            except Exception as e:
                logger.exception("Caught a search product exception.")
                products_information={'data':[]}

            if len(products_information['data'])==0:
                dispatcher.utter_message(output_text_convert("数据库没有找到{%s}，还有什么可以帮您的？"%product))
                return [SlotSet("choice_risk", choice_risk)]

            # print(products_information['data']) 

            products_names = [(e['displayName'],e['id'],interest_display(e['interestRateDisplay']),e['minInvestAmount'],e['riskLevel'],e['investPeriodInDays'],e['productCategory'],e['groupCode']) for e in products_information['data']] 

            msg=str({"LucyID":"123","title":"给您推荐以下产品","cardList":[{'title':e[0],'leftValue':e[2],'leftKey':'起投%s元'%e[3],'rightValue':'风险%s星'%e[4],'rightKey':'期限%s天'%e[5],'note':'','schema':'lufax://financedetail?productid=%s'%e[1]} for e in products_names]})
            dispatcher.utter_message(str({'REC':msg}))
            return [SlotSet("choice_risk", None),SlotSet("choice_product", None),SlotSet("choice_amount", None),SlotSet("product", None),SlotSet("amount", None)]

        elif choice_amount is None and amount is None:
            content="您打算的投资金额："
            link=[{"content":"小于100万","reply":"""/rec_products{"choice_amount":"小于100万"}""","echoReply":"N"},{"content":"大于等于100万","reply":"""/rec_products{"choice_amount":"大于等于100万"}""","echoReply":"N"}]
            msg = """{"content":"%s","link":%s}"""%(content,link)
            dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            return [SlotSet("choice_risk", choice_risk)]
        
        elif choice_risk is None:
            content="您能承受多大的风险："
            link=[{"content":"中高风险","reply":"""/rec_products{"choice_risk":"高"}""","echoReply":"N"},{"content":"低风险","reply":"""/rec_products{"choice_risk":"低"}""","echoReply":"N"}]
            msg = """{"content":"%s","link":%s}"""%(content,link)
            dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            return [SlotSet("choice_risk", choice_risk)]

        elif choice_risk =='高'  and (amount is not None or choice_amount == '小于100万'):
            content="您选择一种产品类型："
            link=[{"content":"公募基金","reply":"""/rec_products{"choice_product":"公募基金"}""","echoReply":"N"},{"content":"爱理财6号","reply":"""/rec_products{"choice_product":"爱理财6号"}""","echoReply":"N"}]
            msg = """{"content":"%s","link":%s}"""%(content,link)
            dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            return [SlotSet("choice_risk", choice_risk)]           
        elif choice_risk=='低' and (amount is not None or choice_amount== '小于100万'):
            content="您选择一种产品类型："
            link=[{"content":"智理财","reply":"""/rec_products{"choice_product":"智理财"}""","echoReply":"N"},{"content":"鑫理财","reply":"""/rec_products{"choice_product":"鑫理财"}""","echoReply":"N"},{"content":"保险定期","reply":"""/rec_products{"choice_product":"保险定期"}""","echoReply":"N"},{"content":"银行存款","reply":"""/rec_products{"choice_product":"银行存款"}""","echoReply":"N"},{"content":"P2P","reply":"""/rec_products{"choice_product":"P2P"}""","echoReply":"N"}]
            msg = """{"content":"%s","link":%s}"""%(content,link)
            dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            return [SlotSet("choice_risk", choice_risk)] 
        elif choice_risk=='低' and choice_amount== '大于等于100万':
            content="您选择一种产品类型："
            link=[{"content":"尊理财","reply":"""/rec_products{"choice_product":"尊理财"}""","echoReply":"N"},{"content":"私理财","reply":"""/rec_products{"choice_product":"私理财"}""","echoReply":"N"},{"content":"信理财","reply":"""/rec_products{"choice_product":"信理财"}""","echoReply":"N"}]
            msg = """{"content":"%s","link":%s}"""%(content,link)
            dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            return [SlotSet("choice_risk", choice_risk)] 
        elif choice_risk =='高' and choice_amount== '大于等于100万':
            content="您选择一种产品类型："
            link=[{"content":"资管","reply":"""/rec_products{"choice_product":"资管"}""","echoReply":"N"},{"content":"私募","reply":"""/rec_products{"choice_product":"私募"}""","echoReply":"N"}]
            msg = """{"content":"%s","link":%s}"""%(content,link)
            dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            return [SlotSet("choice_risk", choice_risk)]
        else:
            content={"content":"下面的产品列表可能有您想要的产品："}
            link=[{"content":"混合产品列表","url":"lufax://financelist?listtype=mixed"}]
            msg=str(dict(content,**{"link":link}))
            dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            return [SlotSet("choice_risk", choice_risk)]

       


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
            content="您好，这里是VIP智能助理，可以解决您对于产品的疑问，请输入您想查询的产品名称 或 点击下列链接了解产品类目"
            link=[{"content":"产品类目(低风险,小于100万)","reply":"""/rec_products{"choice_risk":"低","choice_amount":"小于100万"}""","echoReply":"N"},{"content":"产品类目(低风险,大于等于100万)","reply":"""/rec_products{"choice_risk":"低","choice_amount":"大于等于100万"}""","echoReply":"N"},{"content":"产品类目(中高风险,小于100万)","reply":"""/rec_products{"choice_risk":"高","choice_amount":"小于100万"}""","echoReply":"N"},{"content":"产品类目(中高风险,大于等于100万)","reply":"""/rec_products{"choice_risk":"高","choice_amount":"大于等于100万"}""","echoReply":"N"}]
            msg = """{"content":"%s","link":%s}"""%(content,link)
            dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            if product_intent in PRODUCT_INTENTS:
                return [SlotSet("last_product_intent",product_intent)]
            else:
                return []
        print ("product: "+product_name)

        last_product_information=tracker.get_slot("last_product_information")

        last_product_name=tracker.get_slot("last_product_name")
        print("last_product_name: "+str(last_product_name))


        results = self.search_product_info (dispatcher,tracker,domain,product_intent,last_product_intent,product_name,last_product_name,last_product_information)
        return [SlotSet(key,value) for (key,value) in results[0].items()]

    @staticmethod
    def no_find_product_info (product_name):
        content="没有找到您要查的{%s}产品，请输入您想查询的产品名称 或 点击下列链接了解产品类目"%product_name
        link=[{"content":"产品类目(低风险,小于100万)","reply":"""/rec_products{"choice_risk":"低","choice_amount":"小于100万"}""","echoReply":"N"},{"content":"产品类目(低风险,大于等于100万)","reply":"""/rec_products{"choice_risk":"低","choice_amount":"大于等于100万"}""","echoReply":"N"},{"content":"产品类目(中高风险,小于100万)","reply":"""/rec_products{"choice_risk":"高","choice_amount":"小于100万"}""","echoReply":"N"},{"content":"产品类目(中高风险,大于等于100万)","reply":"""/rec_products{"choice_risk":"高","choice_amount":"大于等于100万"}""","echoReply":"N"}]
        msg = """{"content":"%s","link":%s}"""%(content,link)
        return msg

    def search_product_info (self,dispatcher,tracker,domain,product_intent,last_product_intent,product_name,last_product_name,last_product_information):

        fund_interest_display = lambda e:e['interestRate'] if 'interestRate' in e else 'None'
        fund_period_display = lambda e:e['investPeriod'] if 'investPeriod' in e else 'None'

        try:
            products_information=SearchProductName(keywords = product_name,field="['displayName','id','interestRateDisplay','productCategory','groupCode','investPeriodInDays','openingDate','lastCollectionDate','interestRate','investPeriod']")
        except Exception as e:
            logger.exception("Caught a search product exception.")
            products_information={'data':[]}

        if len(products_information['data'])==0:
            msg = self.no_find_product_info(product_name)
            dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            if product_intent in PRODUCT_INTENTS:
                return [{"last_product_intent":product_intent,"last_product_name":product_name}]
            else:
                return [{"last_product_name":product_name}]

        # print(products_information['data']) 

        products_names = [(e['displayName'],e['score'],e['id'],e['interestRateDisplay'],e['productCategory'],e['groupCode'],e['investPeriodInDays'],e['openingDate'],e['lastCollectionDate'],fund_interest_display(e),fund_period_display(e)) for e in products_information['data']]


        if len(products_information['data'])==0:
            msg = self.no_find_product_info(product_name)
            dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            if product_intent in PRODUCT_INTENTS:
                return [{"last_product_intent":product_intent,"last_product_name":product_name}]
            else:
                return [{"last_product_name":product_name}]


        list_products = [(name, difflib.SequenceMatcher(None, product_name.replace(' ','').lower(), name.replace(' ','').lower()).quick_ratio(),ids,interest,investPeriodInDays,openingDate,lastCollectionDate,productCategory,interestRate,investPeriod) for (name,score,ids,interest,productCategory,groupCode,investPeriodInDays,openingDate,lastCollectionDate,interestRate,investPeriod) in  products_names]
        # list_products = [(name,score,ids,interest,investPeriodInDays) for (name,score,ids,interest,productCategory,groupCode,investPeriodInDays) in  products_names]

        list_products_sorted = sorted(list_products, key=lambda d: d[1], reverse=True)
        # print(list_products_sorted)

        count=0
        tmp_msg=[]

        for e in list_products_sorted:
            if e[1]>0.8:
                try:
                    res = GetProductInfo(e[2])
                    # res = SearchProductName(keywords=e[0],pageIndex=1,pageSize=1)
                except Exception as e:
                    logger.exception("Caught a get product exception.")
                    res={'data':[]}
                if len(res['data'])==0:
                    msg = self.no_find_product_info(product_name)
                    dispatcher.utter_message(str({'CONTENT_LINK':msg}))

                    if product_intent in PRODUCT_INTENTS:
                        return [{"last_product_intent":product_intent,"last_product_name":product_name}]
                    else:
                        return [{"last_product_name":product_name}]                   

                # print(res['data'])
                if product_intent in PRODUCT_INTENTS:
                    self.output_of_intent(dispatcher,tracker,domain,product_intent,res['data'],e[4],e[5],e[6],e[7],e[8],e[9])
                    # print("2222 product_intent:"+product_intent)
                    return [{"last_product_intent":product_intent,"last_product_name":product_name}]
                elif last_product_intent in PRODUCT_INTENTS:
                    self.output_of_intent(dispatcher,tracker,domain,last_product_intent,res['data'],e[4],e[5],e[6],e[7],e[8],e[9])
                    # print("3333 product_intent:"+product_intent)
                    return [{"last_product_name":product_name}]  
                else:
                    # print("4444 product_intent:"+product_intent)
                    content="您想查询{%s}的什么信息呢？ 点击下列链接选择产品信息范围"%product_name
                    link=[{"content":"投资范围,投资策略,投资标的","reply":"""/invest_scope""","echoReply":"N"},{"content":"收益率,历史业绩","reply":"""/invest_return""","echoReply":"N"},{"content":"管理人,管理机构","reply":"""/invest_manager""","echoReply":"N"},{"content":"风险评级","reply":"""/invest_risk""","echoReply":"N"},{"content":"投资期限,赎回时间,到帐时间","reply":"""/invest_period""","echoReply":"N"},{"content":"起投金额,追加金额","reply":"""/invest_amount""","echoReply":"N"},{"content":"募集时间,购买时间,预约时间","reply":"""/invest_time""","echoReply":"N"},{"content":"申赎费用,优惠,折扣","reply":"""/invest_coupon""","echoReply":"N"}]

                    msg = """{"content":"%s","link":%s}"""%(content,link)
                    dispatcher.utter_message(str({'CONTENT_LINK':msg}))

                    return [{"last_product_name":product_name}]
            elif e[1]>0.2: 
                count+=1
                if e[7]!='802':
                    tmp_msg.append({"content":"%s  收益%s 投资%s天"%(e[0],e[3],e[4]),"reply":"%s"%(e[0]),"echoReply":"N"})
                else:
                    tmp_msg.append({"content":"%s  收益%s 投资%s天"%(e[0],e[8],e[9]),"reply":"%s"%(e[0]),"echoReply":"N"})

                if count==5 or count==len(list_products_sorted):
                    content={"content":"您查询{%s}的相似产品如下,请点击链接了解具体信息："%product_name}
                    link={"link":tmp_msg}
                    msg=str(dict(content,**link))                            
                    dispatcher.utter_message(str({'CONTENT_LINK':msg}))
                    if product_intent in PRODUCT_INTENTS:
                        return [{"last_product_intent":product_intent,"last_product_name":product_name}]
                    else:
                        return [{"last_product_name":product_name}]
            else:
                if count>0:
                    content={"content":"您查询{%s}的相似产品如下,请点击链接了解具体信息："%product_name}
                    link={"link":tmp_msg}
                    msg=str(dict(content,**link))                            
                    dispatcher.utter_message(str({'CONTENT_LINK':msg}))
                    if product_intent in PRODUCT_INTENTS:
                        return [{"last_product_intent":product_intent,"last_product_name":product_name}]
                    else:
                        return [{"last_product_name":product_name}]

                msg = self.no_find_product_info(product_name)
                dispatcher.utter_message(str({'CONTENT_LINK':msg}))

                if product_intent in PRODUCT_INTENTS:
                    return [{"last_product_intent":product_intent,"last_product_name":product_name}]
                else:
                    return [{"last_product_name":product_name}]


    def output_of_intent(self,dispatcher,tracker,domain,product_intent,product_information,investPeriodInDays,openingDate,lastCollectionDate,productCategory,interestRate,investPeriod):
        interest_display = lambda x:product_information['interestRateDisplay'] if x != '802' else str(product_information['interestRatePerSevenDay'])
        period_display = lambda x:investPeriodInDays if x != '802' else investPeriod
        
        try:
            if product_intent=='invest_scope' : #'投资范围':
                content={"content":"该{%s}主要投资范围包含基金和债券,为投资者提供长期稳定的回报。近期业绩收益（%s）"%(product_information['displayName'],interest_display(productCategory))}
                link=[{"content":"我要投资{%s}"%product_information['displayName'],"url":"lufax://financedetail?productid=%s"%product_information['id']}]
                msg=str(dict(content,**{"link":link}))
                dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            elif product_intent=='invest_return': #'收益率':
                msg={"content":"{%s}近期的业绩收益（%s）"%(product_information['displayName'],interest_display(productCategory))}
                if productCategory=='802':
                    tmp_msg=[{"content":"我要投资{%s}"%product_information['displayName'],"url":"lufax://financedetail?productid=%s"%product_information['id']},{"content":"{%s}的收益率曲线"%product_information['displayName'],"url":"http://m.lu.com/m-cs/trendchart?productId=%s&type=%s"%(product_information['id'],'NETVALUE')}]
                else:
                    tmp_msg=[{"content":"我要投资{%s}"%product_information['displayName'],"url":"lufax://financedetail?productid=%s"%product_information['id']}]

                msg2={"link":tmp_msg}
                msg=str(dict(msg,**msg2))
                dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            elif product_intent=='invest_manager': #'管理人':
                msg={"content":"该{%s}的管理人是（%s）"%(product_information['displayName'],product_information['fundManager'])}
                tmp_msg=[{"content":"我要投资{%s}"%product_information['displayName'],"url":"lufax://financedetail?productid=%s"%product_information['id']}]
                msg2={"link":tmp_msg}
                msg=str(dict(msg,**msg2))
                dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            elif product_intent=='invest_risk': #'风险':
                msg={"content":"目前所有产品都不能承诺保本保收益，{%s}的风险等级是（%s）星，存在本金亏损的风险"%(product_information['displayName'],product_information['riskLevel'])}
                tmp_msg=[{"content":"我要投资{%s}"%product_information['displayName'],"url":"lufax://financedetail?productid=%s"%product_information['id']}]
                msg2={"link":tmp_msg}
                msg=str(dict(msg,**msg2))
                dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            elif product_intent=='invest_period': #'期限':
                msg={"content":"{%s}的投资期限为（%s）天。"%(product_information['displayName'],period_display(productCategory))}
                tmp_msg=[{"content":"我要投资{%s}"%product_information['displayName'],"url":"lufax://financedetail?productid=%s"%product_information['id']}]
                msg2={"link":tmp_msg}
                msg=str(dict(msg,**msg2))
                dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            elif product_intent=='invest_amount' : #'金额':
                msg={"content":"该{%s}的起投金额为（%s）元，追加金额是（%s）元"%(product_information['displayName'],product_information['minInvestAmount'],product_information['increaseInvestAmount'])}
                tmp_msg=[{"content":"我要投资{%s}"%product_information['displayName'],"url":"lufax://financedetail?productid=%s"%product_information['id']}]
                msg2={"link":tmp_msg}
                msg=str(dict(msg,**msg2))
                dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            elif product_intent=='invest_time': #'募集时间':
                msg={"content":"该{%s}销售时间为（%s）；结束时间为（%s）"%(product_information['displayName'],openingDate,lastCollectionDate)}
                tmp_msg=[{"content":"我要投资{%s}"%product_information['displayName'],"url":"lufax://financedetail?productid=%s"%product_information['id']}]
                msg2={"link":tmp_msg}
                msg=str(dict(msg,**msg2))
                dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            elif product_intent=='invest_coupon': #'优惠':
                msg={"content":"{%s}申购费为（%s）；购买折扣为（%s）；"%(product_information['displayName'],product_information['buyFeeRate'],product_information['buyFeeDiscount'])}
                tmp_msg=[{"content":"我要投资{%s}"%product_information['displayName'],"url":"lufax://financedetail?productid=%s"%product_information['id']}]
                msg2={"link":tmp_msg}
                msg=str(dict(msg,**msg2))
                dispatcher.utter_message(str({'CONTENT_LINK':msg}))
            else:
                dispatcher.utter_template("utter_default",tracker)
        except Exception as e:
            logger.exception("Caught an uncompleted product information  exception.")
            dispatcher.utter_message(output_text_convert("此{%s}的信息没有找到，请尝试其他的" %product_information['displayName']))




def train_dialogue(domain_file="invest_domain.yml",
                   model_path="models/dialogue",
                   training_data_file="data/invest_story.md"):

    fallback = FallbackPolicy(fallback_action_name="action_tuling",
                              # core_threshold=0.90,
                              nlu_threshold=0.85)

    # featurizer = MaxHistoryTrackerFeaturizer(BinarySingleStateFeaturizer(),
    #                                      max_history=3)

    agent = Agent(domain_file,
              policies=[MemoizationPolicy(),
                        KerasPolicy(), fallback])
    # agent = Agent(domain_file,
    #           policies=[MemoizationPolicy(max_history=5),
    #                     KerasPolicy(featurizer)],
    #                     interpreter=interpreter)    
    agent.train(
        training_data_file,
        # max_history=2,
        epochs=300,
        batch_size=32,
        augmentation_factor=50,
        validation_split=0.1
    )
    agent.persist(model_path)
    return agent

if __name__ == '__main__':

    train_dialogue()
