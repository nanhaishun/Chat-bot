## regex:period_feature
- [一二两三四五六七八九十今去明.。|0-9]+(个)?(年|月|天|m|y|d|M|Y|D)+(期)?

## regex:amount_feature
- [一二两三四五六七八九十.。|0-9]+(千|百|万|w|W|元|圆|园)?[一二两三四五六七八九十|0-9]?

## regex:return_feature1
- [一二两三四五六七八九十.。|0-9]+(%|％)+

## regex:return_feature2
- [万千百分之十]+[一二两三四五六七八九十.。|0-9]+[一二两三四五六七八九十|0-9]+


## lookup:product_names
./jieba_userdict/product_dict.txt
