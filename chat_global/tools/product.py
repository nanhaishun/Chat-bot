import random
import json

def compose(i):
    list=[]
    for i in range(i):
         list.append(str[i])
    return list


def to_json(text,str,index):
        python2json ={}
        python3json ={}
        python2json["text"]=text
        python2json["intent"] = intent[j]
        python2json["entities"]=[]
        python3json["start"]=index
        python3json["end"]= python3json["start"]+len(str)
        python3json["value"]=str
        python3json["entity"]="product"
        python2json["entities"].append(python3json)
        return python2json
 
list =[]
with open("/Users/leo/Desktop/json_test/product_dict.txt") as f:
    for line in f.readlines():
        line = line.strip('\n')
        list.append(line)
str=[]
period=[]
##invest_period 
str.append('亲,str那只基金封闭期原来说是一个月，现在过了一个为什么还封闭' )
str.append ('你好，请问str,没到期以前，有什么办法中途取钱出来吗')
str.append ('str，今天可以赎回吗')
str.append ( '昨天中午赎回的str今天还是冻结状态?')
str.append('我购买的str到期为什么没有赎回')
str.append ('看了下11月11日到期str状况，为啥显示0状况')
str.append ('沈老师，我的str可以赎回了吗？')
str.append ('你好，str期限是封闭的')
str.append('请问str的赎回时间是t+1么')
str.append('这个str好像是灵活赎回?')
str.append('我的str5号昨天到期，页面怎么显示仍然在“封闭期”。')
str.append ('请问，str的赎回收费如何？')
str.append('我的那两笔str为什么无法赎回？')
str.append('请问str提前结束是吗？本来到期日是7月中呢，现在显示6月6日，想和你确认呢')

period=compose(len(str))
str=[]

time=[]
#invest_time
str.append('请问今天下午还有str的产品吗？')
str.append('str一般几点啊上架？')
str.append('请问平安金管家中售卖的str投每天什么时间开始发售？每次进去看都售馨')
str.append('最近有str发行吗？')
str.append('节后平安担保的str还没有上架计划')
str.append('最近的str很快给秒，一般产品是几点推出')
str.append('今天的strt+31卖光了')
str.append('你好，最近有str吗')
str.append('近期str的排期，告知我')
str.append('你好！最近还有str的话，请记得通知我，谢谢!')
str.append('我有些偏保守，你能告诉我下次str，是什么时候发行么?')
str.append('啥时候有str上架呀')
str.append('楠楠，有新的str商品吗?')
str.append('为什么今天有str不给我及时打电话通知我呢？再什么时候有，请立即电话通知.')
str.append('中下旬会有更多str产品上线么？')

time =compose(len(str))
str=[]

scope=[]
# #invest_scope
str.append('请问str属于固定理财产品吗？还是属于基金产品')
str.append('能否介绍下str')
str.append('str说到底还是基金')
str.append('str是p2p吗')
str.append('str属于什么性质？')
str.append('定期str，有的话告诉我')
str.append('您说的str回归a股这个产品是基金吗？')
str.append('str是证券类')
str.append('您好请问str是什么类型的项目呀')
str.append('产品结构和以往的str有什么区别？因为名称变化比较多，分不清产品结构')
str.append('是说str还有其他的渠道募集')
str.append('我买的str，它的投资标底是什么？')
str.append('还有，str都是投资啥的')
str.append('你好，请问str，这个标是怎么了，为什么在其它里面')
str.append('我觉得这个时间就ok，不过您说的那个str是什么')
scope=compose(len(str))
str=[]

risk=[]
# #invest_risk
str.append('str风险为中，是否**啊')
str.append('好的，谢谢。是不是str相对来说风险是比较小的呢?')
str.append('str这个风险低一些吧，毕竟是平安旗下的产品')
str.append('我预约的str，风险很大吗？会产生同吉9号、10号的风险吗?')
str.append('你好咨询一下。网贷，str请问这个项目风险大吗？谢谢')
str.append('str这个产品的风险系数，会不会逾期')
str.append('所以str风险很大')
str.append('我昨天误买了一笔str怎么在持有中看不到了，这个风险大吗？要持有多少天才能卖呢?')
str.append('str向特定对象发行，这种发行有无合法性呢？')
str.append('请问，之前短债的收益大概是什么情况，**风险可能是什么？str具体怎么样')
str.append('我预约的str，风险很大吗？会产生同吉9号、10号的风险吗？')
str.append('str，看了说明书，貌似没有抵押物，只有增信措施？你帮忙评估一下风险，说明一下风险提示？谢谢！')
str.append('str风险会是什么')
str.append('str风险等级高吗？')
str.append('str这个项目怎么样风险系数高吗适合投资吗')
risk=compose(len(str))
str=[]


amount=[]
# #invest_amount
str.append('str的起点资金是多少')
str.append('str是一只很不错的基金，可是进去早了两天，想再补一点可以吗?')
str.append('str,最低额度是多少？')
str.append('str？起投金额多少？')
str.append('str正常情况下起投门槛至少多少？')
amount=compose(len(str))
str=[]


coupon=[]
# #invest_coupon
str.append('现在还没看到因为之前str项目备案不成功发的投资券诶')
str.append('str无可用投资劵？')
str.append('现在还没看到因为之前str备案不成功发的投资券诶')
str.append('你好！请问我的str返现券为什么这么久了还没有到?')
str.append('为什么我的str券等了这么久？')
str.append('上次说那个str不是有0.5%的返券吗，怎么到现在还没有？')
str.append('亲，上次买的str今天起息了，那么他返的券什么时候到位？')
str.append('当时买的str返券什么时候呀？')
str.append('能送我str产品的投资券')
str.append('上次买的str，4月21日已成立，好久送券呢')
str.append('10申购str是因为资金没到绑定卡??但是200券给浪费了')
str.append('你好，我购买str，能给些抵用券吗')
str.append('贾经理好，如果购入str有投资券返还没?')
str.append('张经理，你原来说买str产品有积分赠送，还有那0.2%的投资券，为何都不见踪影？??')
str.append('那笔str应该有返券是吗一会帮我看下微信回复我就好谢谢')
coupon=compose(len(str))
str=[]


ireturn=[]
#invest_return
str.append('str的收益不固定?')
str.append('str，可以吗？\n利率是固定的吗？')
str.append('str这个没看懂！它的基金净值只有1.28!折算成年利率是多少？')
str.append('str，预期收益目标是多少。')
str.append('请给我发一个str的每月不复投的扣除转让手续费的实际利率表')
str.append('str这个如何？我看收益明显高出来很多7天的')
str.append('这str利率怎么这么高')
str.append('帖曼，你们的str收益怎么样')
str.append('哦，但看收益率好像是str比较高，是看收益率吗？')
str.append('你说的str，保底是由上市公司回购吗？保底年净收益率是多少')
str.append('亲爱的上次问过你str扣完信息费，折合年化收益多少啦?')
str.append('那str是不是都是固定收益的')
str.append('利率还不如投str高?')
str.append('str好像利率不高')
str.append('今天的str是多少利率啊？')
ireturn=compose(len(str))
str=[]


manage=[]
#invest_manager
str.append('马上要发行的str，管理人托管方都是平安吧？？')
str.append('我看到的新闻，该str就是我刚在陆交所购买的资管产品方啊')
str.append('我们这个经费是给了鼎辉？它是str投资方')
str.append('谁负责管理str')
str.append('str的资金托管是谁啊，陆金所只是做销售这块是吗？')
str.append('str是什么？基金管理人到底是谁？')
str.append('这个str是由哪个监管部门管理？')
str.append('你们是负责str的管理人吧')
str.append('str是什么公司发布的？')
str.append('那么这次str的运营方是谁？')
str.append('你好，冀经理！你发来的str资料中提到没有成功上市，则项目方提供8%单利回购，这里的项目方是指的协鑫集团吗？')
manage=compose(len(str))
str=[]


intent =[]
##intent
intent.append('invest_period')
intent.append('invest_time')
intent.append('invest_scope')
intent.append('invest_risk')
intent.append('invest_amount')
intent.append('invest_coupon')
intent.append('invest_return')
intent.append('invest_manager')


x=0
unique_number =set()
i=0
final_list=[]


S =set()

while i<len(list):
    j=0
    str =list[i]
    while x<3:
        j = random.randint(0,7)
        if j in S:
            j = random.randint(0,7)
        S.add(j)    
        if(j==0):
            temp=len(period)
            k = random.randint(0,temp-1)
            index  = period[k].index('s')
            period[k]=period[k].replace('str',str)
            temp = to_json(period[k],str,index)
            final_list.append(temp)
            period[k]=period[k].replace(str,'str')
            x = x+1
        if(j==1):
            temp=len(time)
            k = random.randint(0,temp-1)
            index  = time[k].index('s')
            time[k]=time[k].replace('str',str)
            temp = to_json(time[k],str,index)
            final_list.append(temp)
            time[k]=time[k].replace(str,'str')
            x = x+1      
        if(j==2):
            temp=len(scope)
            k = random.randint(0,temp-1)
            index  = scope[k].index('s')
            scope[k]=scope[k].replace('str',str)
            temp = to_json(scope[k],str,index)
            final_list.append(temp)
            scope[k]=scope[k].replace(str,'str')
            x = x+1     
        if(j==3):
            temp=len(risk)
            k = random.randint(0,temp-1)
            index  = risk[k].index('s')
            risk[k]=risk[k].replace('str',str)
            temp = to_json(risk[k],str,index)
            final_list.append(temp)
            risk[k]=risk[k].replace(str,'str')
            x = x+1
        if(j==4):
            temp=len(amount)
            k = random.randint(0,temp-1)
            index  = amount[k].index('s')
            amount[k]=amount[k].replace('str',str)
            temp = to_json(amount[k],str,index)
            final_list.append(temp)
            amount[k]=amount[k].replace(str,'str')
            x = x+1  
        if(j==5):
            temp=len(coupon)
            k = random.randint(0,temp-1)
            index  = coupon[k].index('s')
            coupon[k]=coupon[k].replace('str',str)
            temp = to_json(coupon[k],str,index)
            final_list.append(temp)
            coupon[k]=coupon[k].replace(str,'str')
            x = x+1
        if(j==6):
            temp=len(ireturn)
            k = random.randint(0,temp-1)
            index  = ireturn[k].index('s')
            ireturn[k]=ireturn[k].replace('str',str)
            temp = to_json(ireturn[k],str,index)
            final_list.append(temp)
            ireturn[k]=ireturn[k].replace(str,'str')
            x = x+1      
        if(j==7):
            temp=len(manage)
            k = random.randint(0,temp-1)
            index  = manage[k].index('s')
            manage[k]=manage[k].replace('str',str)
            temp = to_json(manage[k],str,index)
            final_list.append(temp)
            manage[k]=manage[k].replace(str,'str')
            x = x+1                  
        else: 
            continue

    S.clear()            
    x=0          
    i = i+1

w =open("/Users/leo/Desktop/json_test/final.txt","w") 
w.write(json.dumps(final_list,ensure_ascii=False,indent=4))

w.close()
f.close()


    