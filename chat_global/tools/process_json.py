import simplejson as json 
from random import sample
import os.path

# 遍历指定目录，显示目录下的所有文件名
def eachFile(filepath):
    pathDir =  os.listdir(filepath)
    for allDir in pathDir:
        child = os.path.join('%s/%s' % (filepath, allDir))
        if os.path.isfile(child):
            arr.append(child)
#             print child.decode('gbk') # .decode('gbk')是解决中文显示乱码问题
            continue
        eachFile(child)

# merge multiple json files or not
if 1:
    filenames = '../tmp' # refer root dir
    arr=[]
    eachFile(filenames)
    for i in arr:
        print (i)

    dd={"rasa_nlu_data":{"common_examples":[],"regex_features":[],"entity_synonyms":[]}}
    l_tmp=[]

    for i in arr:    
        f=open(i,"r",encoding='utf-8')
        ddata = json.loads(f.read()) 
        l_tmp.extend(ddata["rasa_nlu_data"]["common_examples"]) 
        f.close()
else:
    dd={"rasa_nlu_data":{"common_examples":[]}}
    f=open("../final[1].json","r",encoding='utf-8')
    ddata = json.loads(f.read())
    l_tmp= ddata["rasa_nlu_data"]["common_examples"] 
    f.close()

# filter intent or not
if 0:
    l=[]
    for e in l_tmp:
        # if e["intent"].strip()!='' and e["intent"].strip().find('+')<0:
        # if e["intent"] in ['投资范围','收益率','管理人','风险','期限','金额','募集时间','优惠']:
        if e["intent"] in ['rec_products']:
            l.append(e)
else:
    l=l_tmp

# split train/test files or not
if 0:
    index_r1 = sample(range(len(l)), int(len(l)*0.8))

    remain_index = tuple(set(range(len(l))) - set(index_r1))

    print(len([l[i] for i in index_r1]))

    print(len([l[i] for i in remain_index]))
    #print(len(l_new))
    dd["rasa_nlu_data"]["common_examples"]=[l[i] for i in remain_index]
    f2=open("./test.json","w",encoding='utf-8')
    f2.write(json.dumps(dd,sort_keys=True,indent=4,ensure_ascii=False))
    dd["rasa_nlu_data"]["common_examples"]=[l[i] for i in index_r1]
    f3=open("./train.json","w",encoding='utf-8')
    f3.write(json.dumps(dd,sort_keys=True,indent=4,ensure_ascii=False))
    # f.close()
    f2.close()
    f3.close()
else:
    print(len(l))

    #print(len(l_new))
    dd["rasa_nlu_data"]["common_examples"]=l
    f2=open("../tmp/test.json","w",encoding='utf-8')
    f2.write(json.dumps(dd,sort_keys=True,indent=4,ensure_ascii=False))
    # f.close()
    f2.close()
