

with open ('../jieba_userdict/product_dict.txt','r') as source1, open ('../jieba_userdict/new_productname.txt','w') as destination:
    file=source1.readlines()


    for line in file:
        line="- ["+line.replace('\n','')+"](product)"
        destination.write(line+'\n')
