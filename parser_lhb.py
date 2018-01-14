# -*- coding: utf-8 -*-

from bs4 import BeautifulSoup
import csv
import sys
import json
import base64
import zlib
import os
class THSLHB(object):
    def __init__(self):
        self.__code = ''
        self.__name = ''
        self.__url = ''
        self.__flag = 0
        self.__flag_name = ''

    def code(self):
        return self.__code

    def name(self):
        return self.__name

    def url(self):
        return self.__url

    def flag(self):
        return self.__flag

    def flag_name(self):
        return self.__flag_name

    def set_name(self, name):
        self.__name = name

    def set_url(self, url):
        self.__code = url.split('/')[-2]
        self.__url = url

    def set_flag_name(self, flag_name):
        self.__flag_name = flag_name
        if flag_name == u'一线游资':
            self.__flag = 1
        elif flag_name == u'知名游资':
            self.__flag = 2
        elif flag_name == u'敢死队':
            self.__flag = 3
        elif flag_name == u'跟风高手':
            self.__flag = 4
        elif flag_name == u'毒瘤':
            self.__flag = 5
        elif flag_name == u'新股专家':
            self.__flag = 6


class ParserLHBData(object):
    def __init__(self):
        self.__lhb_dict = {}

    def dump(self):
        record_fieldname = ['code', 'name', 'flag_name', 'flag', 'url']

        with open('ths_lhb_detail.csv','w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=record_fieldname)
            writer.writeheader()
            for k, lhb in self.__lhb_dict.items():
                writer.writerow({'code':lhb.code(), 'name':lhb.name(),
                                 'flag_name':lhb.flag_name(),'flag':lhb.flag(),
                                 'url':lhb.url()})

    def inline_html_to_ths(self, unit):
        ths_lhb = THSLHB()
        info = unit.contents[0]
        url = info.attrs['href']
        name = info.contents[0]
        if len(unit.contents) > 1:
            flag_name = unit.contents[1].text
            ths_lhb.set_flag_name(flag_name)
        ths_lhb.set_name(name)
        ths_lhb.set_url(url)
        self.__lhb_dict[ths_lhb.code()] = ths_lhb

    def html_to_ths(self, unit):
        ths_lhb = THSLHB()
        info = unit.contents[0]
        attrs = info.attrs
        url = attrs['href']
        title = attrs['title']
        ths_lhb.set_name(title)
        ths_lhb.set_url(url)
        if len(unit.contents) > 2:
            flag = unit.contents[2].text
            ths_lhb.set_flag_name(flag)
        self.__lhb_dict[ths_lhb.code()] = ths_lhb


    def parser_file_lhb(self, file, ths_type):
        file_object = open(file, 'rb')
        all_the_test = file_object.read()
        ob = json.loads(all_the_test)
        charset = ob['charset']
        content = base64.b32decode(ob['content'])
        content = zlib.decompress(content)
        content = content.decode(charset)
        if ths_type == 'sbcs' or ths_type == 'zjsl':
            lhb_parser.parser_ths(content, 0)
        elif ths_type =='btcz':
            lhb_parser.parser_ths_pair(content)
        elif ths_type == 'orgcode':
            lhb_parser.parser_ths(content, 1)
        file_object.close()

    def parser_ths_pair(self, all_the_test):

        soup = BeautifulSoup(all_the_test, 'html.parser')
        tbody = soup.select('tbody')[0].contents
        i = 0
        for tag_unit in tbody:
            if i % 2 == 0:
                i += 1
                continue
            self.html_to_ths(tag_unit.contents[3])
            self.html_to_ths(tag_unit.contents[7])
            i += 1

    def parser_ths(self, all_the_test, flag_unit = 0):
        soup = BeautifulSoup(all_the_test, 'html.parser')
        tbody = soup.select('tbody')[0].contents
        i = 0
        for tag_unit in tbody:
            if i % 2 == 0:
                i += 1
                continue
            if flag_unit == 0:
                self.html_to_ths(tag_unit.contents[3])
            else:
                self.inline_html_to_ths(tag_unit.contents[1])
            i += 1
    
    def start(self, dir, ftype):
        fdir = dir + '/' + ftype
        for path, dirs, fs in os.walk(fdir):
            for f in fs:
                filename = os.path.join(path, f)
                print (filename)
                self.parser_file_lhb(filename, ftype)
                # print (filename)

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    lhb_parser = ParserLHBData()
    # lhb_parser.start('../../data/nirvana/ths/','sbcs')
    # lhb_parser.start('../../data/nirvana/ths/', 'zjsl')
    # lhb_parser.start('../../data/nirvana/ths/', 'btcz')
    lhb_parser.start('../../data/nirvana/ths/','orgcode')
    # lhb_parser.parser_ths('1.html', 0)
    # lhb_parser.parser_ths('2.html', 0)
    # lhb_parser.parser_ths('4.html', 1)
    # lhb_parser.parser_ths_pair('3.html')

    lhb_parser.dump()
