with open ('invest_story_new.md','w') as destination:
    pass

with open ('invest_story.md','r') as source1, open ('invest_story_new.md','a') as destination:
    file=source1.readlines()
    #print(str(file))
    #print(eval("u"+"\'"+str(file)+"\'"))

    for line in file:
        line=line.replace('\n','')
        destination.write(eval("u"+"\'"+str(line)+"\'"))
        destination.write('\n')