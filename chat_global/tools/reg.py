import re
#pattern = re.compile(ur'风险')
pattern = re.compile('[大|小]')
s = u'风险 少 大 多 高低 小'
# s = "adfad asdfasdf asdfas asdfawef asd adsfas "
print(pattern.findall(s))