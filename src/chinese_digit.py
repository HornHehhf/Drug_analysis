#!/usr/bin/env python
# coding: utf-8
# author: binux(17175297.hk@gmail.com)

dict ={u'零': 0, u'一': 1, u'二': 2, u'三': 3, u'四': 4, u'五': 5, u'六': 6, u'七': 7, u'八': 8, u'九': 9, u'十': 10,
       u'壹': 1, u'贰': 2, u'叁': 3, u'肆': 4, u'伍': 5, u'陆': 6, u'柒': 7, u'捌': 8, u'玖': 9, u'拾': 10, u'两': 2}


def getResultForDigit(a, encoding="utf-8"):
    #if isinstance(a, str):
        #a = a.decode(encoding)

    count = 0
    result = 0
    tmp = 0
    Billion = 0
    while count < len(a):
        tmpChr = a[count]
        #print tmpChr
        tmpNum = dict.get(tmpChr, None)
        #如果等于1亿
        if tmpNum == 100000000:
            result = result + tmp
            result = result * tmpNum
            #获得亿以上的数量，将其保存在中间变量Billion中并清空result
            Billion = Billion * 100000000 + result
            result = 0
            tmp = 0
        #如果等于1万
        elif tmpNum == 10000:
            result = result + tmp
            result = result * tmpNum
            tmp = 0
        #如果等于十或者百，千
        elif tmpNum >= 10:
            if tmp == 0:
                tmp = 1
            result = result + tmpNum * tmp
            tmp = 0
        #如果是个位数
        elif tmpNum is not None:
            tmp = tmp * 10 + tmpNum
        count += 1
    result = result + tmp
    result = result + Billion
    return result

