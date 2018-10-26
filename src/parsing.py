#!/usr/bin/env python
# -*- coding: utf-8 -*-
from os import listdir
import sys
import re
import json
from stanfordcorenlp import StanfordCoreNLP
from chinese_digit import getResultForDigit
import unicodedata
import csv
from MyHTMLParser import MyHTMLParser

#helper functions
from util import *

DRUG_NAMES = ["鸦片", "吗啡", "海洛因", "大麻", "杜冷丁", "古柯叶", "可卡因", "冰毒", "摇头丸", "K粉", "兴奋剂", "甲基苯丙胺",
                 "麻古", "四氢大麻酚", "甲基本丙胺", "氯胺酮", "盐酸曲马多", "罂粟", "大麻烟", "曲马多"]

def get_text(dir_path):
    #dir_path = 'xj_drugs'
    files = listdir(dir_path)
    for file in files:
        tmp_file = dir_path + '/' + file
        fin = open(tmp_file)
        html = "".join(fin.readlines())
        savedStdout = sys.stdout
        with open('corpus/' + file.split('.')[0] + '.txt', 'w+') as f:
            sys.stdout = f
            parser = MyHTMLParser()
            parser.feed(html)
        sys.stdout = savedStdout
        print('This message is for screen!')

def extract_information(dir_path, info_path, drug_name):
    fout = open(info_path, 'w')
    files = list(set(listdir(dir_path)))
    
    file_num = 0
    for file in files:
        print(file)
        info = {}
        info['doc'] = file.split('.')[0] + '.html'
        file_num += 1
        tmp_file = dir_path + '/' + file
        fin = open(tmp_file)
        lines = fin.readlines()
        lines = [line.strip() for line in lines[0:]]
        '''if "一审" in lines[0]:  # consider more phrases
            info['trial.phase'] = "一审"
        else:
            info['trial.phase'] = ""
        if "判决" in lines[0]:
            info['trial.instrument'] = "判决"
        info['publish.date'] = lines[1].split('：')[1]
        info['court.name'] = lines[2].strip()
        info['case.name'] = lines[4].strip()'''
        info['def.name'] = lines[0]

        # initializes all the indices to 0
        
        info, idx_dict = find_indices(lines, info)

        pun_start = idx_dict['pun_start']
        pun_end = idx_dict['pun_end']
        judge_index = idx_dict['judge_index']
        secretary_index = idx_dict['secretary_index']
        def_start = idx_dict['def_start']
        def_end = idx_dict['def_end']

        if pun_end == 0:
            pun_end = judge_index

        info['pun'] = []        

        # add pun lines to info
        temp_lines = lines[pun_start:pun_end]
        info = add_pun(temp_lines, info)

        # make use of pun to add drug
        info = add_drug(info)
        # if there is no 净重, we should add 克
        info = add_drug_weight(info)
        info = add_drug_weight_from_lines_1(lines, info)        
        # get crime if  without 审查查明 和 pun
        info = add_drug_weight_from_lines_2(lines, info)
        
        # if there is no 净重, we should add 克 in all sentences
        info = add_drug_weight_from_all_sentences(lines, info)

        # find all judge names, juror names and secretary name
        temp_lines = lines[judge_index: secretary_index - 1]
        info, judge_name_list = add_judge_joror_names(temp_lines, info)
        info = add_ruling_date(lines, info)
        info = add_secretary(lines, info)

        # find all defendants' names
        temp_lines = lines[def_start: def_end]
        info = add_def_att_names(temp_lines, info)

        #for line in lines[6:]:
            #if '被告人的身份证明' in line:
                #info['def'] += ':::' + line
        '''pattern = "指派检察员([\u4e00-\u9fff]+)出庭"
        match = re.search(pattern, lines[def_end])
        if match is not None:
            info['prosecutor'] = match.group(1)'''
        while len(judge_name_list) < 3:
            judge_name_list.append("")
        info['judge1.name'] = judge_name_list[0]
        info['judge2.name'] = judge_name_list[1]
        info['judge3.name'] = judge_name_list[2]

        info = add_attitude(lines, info)
        
        # write the info
        fout.write('Case: ' + str(file_num) + "\n")
        for key in info.keys():
            if key == 'def' or key == 'pun' or key == 'drug.type' or key == 'drug.weight':
                fout.write(key + ": " + "\t".join(info[key]) + "\n")
            else:
                fout.write(key + ": " + str(info[key]) + "\n")
        fout.write("\n")


def run_extract_information():
    # dir_path = 'data/corpus'
    # info_path = 'data/info.txt'
    dir_path = '../provinces/samples/all_drugs_samples'
    info_path = 'data/provinces/all_samples_info.txt'
    extract_information(dir_path, info_path, DRUG_NAMES)


def get_type_quantity_distance(drug_type, drug_weight, crime):
    type_index_list = [m.start() for m in re.finditer(drug_type, crime)]
    weight_index_list = [m.start() for m in re.finditer(drug_weight, crime)]
    min_distance = float('inf')
    for type_index in type_index_list:
        for weight_index in weight_index_list:
            if type_index < weight_index:
                distance = weight_index - type_index - len(drug_type)
            else:
                distance = type_index - weight_index - len(drug_weight) + 5  # if type is behind, it has penalty
            if distance < min_distance:
                min_distance = distance
    return min_distance


def get_drug_quantity(drug_type_list, drug_weight_list, crime):
    type_quantity = {}
    for drug_type in set(drug_type_list):
        drug_quantity = ''
        min_distance = float('inf')
        for drug_weight in set(drug_weight_list):
            distance = get_type_quantity_distance(drug_type, drug_weight, crime)
            if distance < min_distance:
                min_distance = distance
                drug_quantity = drug_weight
        type_quantity[drug_type] = drug_quantity
    return type_quantity


def select_drug_quantity(person, info, defendants):
    print(defendants)
    drug_weights = info['drug.weight']
    person_drug_weights = []
    crime = info['crime']
    for drug_weight in set(drug_weights):
        weight_index_list = [m.start() for m in re.finditer(drug_weight, crime)]
        for weight_index in weight_index_list:
            min_distance = float('inf')
            min_def = ""
            for defendant in defendants:
                def_index_list = [m.start() for m in re.finditer(defendant[0], crime)]
                for def_index in def_index_list:
                    if def_index < weight_index:
                        distance = weight_index - def_index
                    else:
                        distance = def_index - weight_index - len(drug_weight) + 5  # if type is behind, it has penalty
                    if distance < min_distance:
                        min_distance = distance
                        min_def = defendant
            if min_def == person or min_def == "":
                person_drug_weights.append(drug_weight)
    return list(set(person_drug_weights))


def get_def_name(info, nlp):
    names = []
    # get def name
    for item_index in range(len(info['def'])):
        item = {'def.name': ""}
        if 'def' in info:
            def_name = info['def'][item_index] + "\n"
            pattern = '被告人[：]?([\u2e80-\u9fffxX×＊·ⅹ.*]+)[0-9（，\n,( \uff3b犯]'
            match = re.search(pattern, def_name)
            if match is not None:
                item['def.name'] = match.group(1)
                if info['doc'] == '3538c56f-c136-4ba5-8d6d-b195bc5c16dc.html':
                    print(item['def.name'])
                if "犯" in item['def.name']:
                    item['def.name'] = item['def.name'].split("犯")[0]
                if "辩" in item['def.name']:
                    item['def.name'] = item['def.name'].split("辩")[0]
                if info['doc'] == '3538c56f-c136-4ba5-8d6d-b195bc5c16dc.html':
                    print(item['def.name'])
                original_name = item['def.name']
                # correct by info['def.name']
                start_char = item['def.name'][0]
                name_len = len(item['def.name'])
                head_index = info['def.name'].find(start_char)
                if head_index != -1:
                    new_name = info['def.name'][head_index: head_index + name_len]
                    flag_mou = False
                    for char in original_name:
                        if char in "xX×＊ⅹ*某犯贩":
                            flag_mou = True
                            break
                    if flag_mou:
                        item['def.name'] = new_name
                    flag_fan = False
                    for char in new_name:
                        if char in "犯贩":
                            flag_fan = True
                            break
                    if flag_fan:
                        item['def.name'] = original_name
                else:
                    # print(item['doc'])
                    # print(item['def.name'])
                    # print(info['def.name'])
                    words = nlp.ner(info['def.name'])
                    ner_def_names = []
                    for word_tuple in words:
                        if word_tuple[1] == "PERSON":
                            ner_def_names.append(word_tuple[0])
                    if item_index < len(ner_def_names):
                        item['def.name'] = ner_def_names[item_index]
                        # print(item['def.name'])
                    else:
                        # error caused by fan
                        fan_index = info['def.name'].find('犯')
                        if fan_index != -1:
                            item['def.name'] = info['def.name'][:fan_index]
                        # print(item['def.name'])
                        # if original_name != item['def.name']:
                        # print(item['doc'])
                        # print(original_name)
                        # print(item['def.name'])
                        # print(info['def.name'])
                        # else:
                        # print(info['def'][item_index])
                        # for char in info['def'][item_index]:
                        # print(char.encode("unicode_escape"))
            else:
                words = nlp.ner(info['def.name'])
                ner_def_names = []
                for word_tuple in words:
                    if word_tuple[1] == "PERSON":
                        ner_def_names.append(word_tuple[0])
                if len(ner_def_names) != 0:
                    item['def.name'] = ner_def_names[item_index]
                    # print(item['def.name'])
                #  error caused by fan
                if "犯" in item['def.name']:
                    item['def.name'] = item['def.name'].split("犯")[0]
                else:
                    fan_index = info['def.name'].find('犯')
                    if fan_index != -1:
                        item['def.name'] = info['def.name'][:fan_index]
        else:
            # print(info['def.name'])
            # print(info['doc'])
            words = nlp.ner(info['def.name'])
            ner_def_names = []
            for word_tuple in words:
                if word_tuple[1] == "PERSON":
                    ner_def_names.append(word_tuple[0])
            if len(ner_def_names) != 0:
                item['def.name'] = ner_def_names[item_index]
                # print(item['def.name'])
            # error caused by fan
            if "犯" in item['def.name']:
                item['def.name'] = item['def.name'].split("犯")[0]
            if info['doc'] == '3538c56f-c136-4ba5-8d6d-b195bc5c16dc.html':
                print(item['def.name'])
            else:
                fan_index = info['def.name'].find('犯')
                if fan_index != -1:
                    item['def.name'] = info['def.name'][:fan_index]
                    # print(item['def.name'])
                    # print(item['def.name'])
                    # if item['def.name'] == "" and item_index < len(ner_def_names):
                    # item['def.name'] = ner_def_names[item_index]
                    # print(item['def.name'])
        if item['def.name'] != "":
            names.append(item['def.name'])
    return names


def get_items(info_path, items_path):
    nlp = StanfordCoreNLP('/Users/hangfeng/HornHe/code/stanford-corenlp-full-2018-02-27', lang='zh')

    drug_dict = {"鸦片": 'opium', "海洛因": 'heroin', "大麻": 'marijuana', "兴奋剂": 'meth', "可卡因": 'cocaine',
                 "甲基苯丙胺": 'meth', "冰毒": 'meth', "甲基本丙胺": 'meth'}
    # "吗啡": 'morphia', "那可汀": 'narcotine', "摇头丸": 'MDMA', "古柯叶": 'coca leaves'
    current_focus = ['doc',
                     'judge1.name', 'judge1.ethnic', 'judge2.name', 'judge2.ethnic', 'judge3.name', 'judge3.ethnic',
                     'def.name', 'def.name.prev', 'def.ethnicity', 'def.recid', 'def.goodattitude', 'def.pleadnotguity',
                     'drug.opium', 'drug.opium.quantity', 'drug.heroin', 'drug.heroin.quantity', 'drug.marijuana',
                     'drug.marijuana.quantity', 'drug.meth', 'drug.meth.quantity', 'drug.cocaine',
                     'drug.cocaine.quantity', 'drug.other.name', 'drug.other.quantity',
                     'pun.fiximpris.length', 'pun.lifeimpris', 'pun.death', 'crime.drug.manufacture',
                     'crime.drug.traffic', 'crime.drug.smuggle', 'crime.drug.transport', 'crime.drug.possession']
    fin = open(info_path)
    lines = fin.readlines()
    lines = [line.strip() for line in lines]
    info_list = []
    info = {}
    for line in lines:
        if len(line) == 0:
            info_list.append(info)
            info = {}
        else:
            content = line.split(':')
            info[content[0]] = content[1][1:]
    for info in info_list:
        if 'def' in info:
            raw_def = info['def'].split('\t')
            info['def'] = raw_def
        if 'pun' in info:
            raw_pun = info['pun'].split('\t')
            info['pun'] = raw_pun
        if 'drug.type' in info:
            raw_drug_type = info['drug.type'].split('\t')
            info['drug.type'] = raw_drug_type
        if 'drug.weight' in info:
            raw_drug_weight = info['drug.weight'].split('\t')
            info['drug.weight'] = raw_drug_weight
    items = {}
    doc_num = 0
    for info in info_list:
        doc_num += 1
        #print(doc_num)
        if 'def' not in info:
            item_num = 1
        else:
            item_num = len(info['def'])
        item_list = []
        #ner_def_names = []
        #words = nlp.ner(info['def.name'])
        #print(words)
        #for word_tuple in words:
            #if word_tuple[1] == "PERSON":
                #ner_def_names.append(word_tuple[0])
        if item_num > 1:
            defendants = get_def_name(info, nlp)
        for item_index in range(item_num):
            item = {}
            for key in current_focus:
                item[key] = ""
            for key in info.keys():
                if key in current_focus:
                    item[key] = info[key]

            # get judge ethnic
            if item['judge1.name'] != "":
                if len(item['judge1.name']) > 3:
                    item['judge1.ethnic'] = '1'
                else:
                    item['judge1.ethnic'] = '0'
            if item['judge2.name'] != "":
                if len(item['judge2.name']) > 3:
                    item['judge2.ethnic'] = '1'
                else:
                    item['judge2.ethnic'] = '0'
            if item['judge3.name'] != "":
                if len(item['judge3.name']) > 3:
                    item['judge3.ethnic'] = '1'
                else:
                    item['judge3.ethnic'] = '0'

            # get def name
            if 'def' in info:
                def_name = info['def'][item_index] + "\n"
                pattern = '被告人[：]?([\u2e80-\u9fffxX×＊·ⅹ.*]+)[0-9（，\n,( \uff3b犯]'
                match = re.search(pattern, def_name)
                if match is not None:
                    item['def.name'] = match.group(1)
                    if info['doc'] == '3538c56f-c136-4ba5-8d6d-b195bc5c16dc.html':
                        print(item['def.name'])
                    if "犯" in item['def.name']:
                        item['def.name'] = item['def.name'].split("犯")[0]
                    if "辩" in item['def.name']:
                        item['def.name'] = item['def.name'].split("辩")[0]
                    if info['doc'] == '3538c56f-c136-4ba5-8d6d-b195bc5c16dc.html':
                        print(item['def.name'])
                    original_name = item['def.name']
                    # correct by info['def.name']
                    print(info)
                    print(item['def.name'])
                    start_char = item['def.name'][0]
                    name_len = len(item['def.name'])
                    head_index = info['def.name'].find(start_char)
                    if head_index != -1:
                        new_name = info['def.name'][head_index: head_index + name_len]
                        flag_mou = False
                        for char in original_name:
                            if char in "xX×＊ⅹ*某犯贩":
                                flag_mou = True
                                break
                        if flag_mou:
                            item['def.name'] = new_name
                        flag_fan = False
                        for char in new_name:
                            if char in "犯贩":
                                flag_fan = True
                                break
                        if flag_fan:
                            item['def.name'] = original_name
                    else:
                        #print(item['doc'])
                        #print(item['def.name'])
                        #print(info['def.name'])
                        words = nlp.ner(info['def.name'])
                        ner_def_names = []
                        for word_tuple in words:
                            if word_tuple[1] == "PERSON":
                                ner_def_names.append(word_tuple[0])
                        if item_index < len(ner_def_names):
                            item['def.name'] = ner_def_names[item_index]
                            # print(item['def.name'])
                        else:
                            # error caused by fan
                            fan_index = info['def.name'].find('犯')
                            if fan_index != -1:
                                item['def.name'] = info['def.name'][:fan_index]
                        #print(item['def.name'])
                    #if original_name != item['def.name']:
                        #print(item['doc'])
                        #print(original_name)
                        #print(item['def.name'])
                        #print(info['def.name'])
                #else:
                    #print(info['def'][item_index])
                    #for char in info['def'][item_index]:
                        #print(char.encode("unicode_escape"))
                else:
                    words = nlp.ner(info['def.name'])
                    ner_def_names = []
                    for word_tuple in words:
                        if word_tuple[1] == "PERSON":
                            ner_def_names.append(word_tuple[0])
                    if len(ner_def_names) != 0:
                        item['def.name'] = ner_def_names[item_index]
                        # print(item['def.name'])
                    # error caused by fan
                    if "犯" in item['def.name']:
                        item['def.name'] = item['def.name'].split("犯")[0]
                    else:
                        fan_index = info['def.name'].find('犯')
                        if fan_index != -1:
                            item['def.name'] = info['def.name'][:fan_index]
            else:
                #print(info['def.name'])
                #print(info['doc'])
                words = nlp.ner(info['def.name'])
                ner_def_names = []
                for word_tuple in words:
                    if word_tuple[1] == "PERSON":
                        ner_def_names.append(word_tuple[0])
                if len(ner_def_names) != 0:
                    item['def.name'] = ner_def_names[item_index]
                    #print(item['def.name'])
                # error caused by fan
                if "犯" in item['def.name']:
                    item['def.name'] = item['def.name'].split("犯")[0]
                if info['doc'] == '3538c56f-c136-4ba5-8d6d-b195bc5c16dc.html':
                    print(item['def.name'])
                else:
                    fan_index = info['def.name'].find('犯')
                    if fan_index != -1:
                        item['def.name'] = info['def.name'][:fan_index]
                    #print(item['def.name'])
                #print(item['def.name'])
            #if item['def.name'] == "" and item_index < len(ner_def_names):
                #item['def.name'] = ner_def_names[item_index]
                #print(item['def.name'])

            # get def ethnic
            if 'def' in info:
                def_name = info['def'][item_index] + "\n"
                pattern = '，([\u2e80-\u9fff]+)族'
                match = re.search(pattern, def_name)
                if match is not None:
                    item['def.ethnicity'] = match.group(0)[1:]
            if item['def.ethnicity'] == "":
                if len(item['def.name']) > 3:
                    item['def.ethnicity'] = '少数民族'
                else:
                    item['def.ethnicity'] = '汉族'

            # add def minority
            if item['def.ethnicity'] == '汉族':
                item['def.minority'] = 0
            else:
                item['def.minority'] = 1
            # get def previous name

            if 'def' in info:
                def_name = info['def'][item_index] + "\n"
                pattern = '(曾用名|别名|绰号|自称|别名|外号|经名|化名|又名|汉名|小名)([:：“])?([\u2e80-\u9fff]+)[,，)]?'
                match = re.search(pattern, def_name)
                if match is not None:
                    if item['def.name.prev'] != "":
                        item['def.name.prev'] = item['def.name.prev'] + '、' + match.group(3)
                    else:
                        item['def.name.prev'] = match.group(3)

            # get drug type
            item['drug.opium'] = '0'
            item['drug.heroin'] = '0'
            item['drug.marijuana'] = '0'
            item['drug.meth'] = '0'
            item['drug.cocaine'] = '0'
            item['drug.other.name'] = []
            if 'drug.type' in info:
                for drug_type in info['drug.type']:
                    if drug_type in drug_dict:
                        item['drug.' + drug_dict[drug_type]] = '1'
                    else:
                        item['drug.other.name'].append(drug_type)
            if len(item['drug.other.name']) == 0:
                item['drug.other.name'] = ""
            else:
                item['drug.other.name'] = " ".join(list(set(item['drug.other.name'])))

            # get drug quantity
            if 'drug.weight' in info and 'drug.type' in info:
                if item_num > 1:
                    # should add name information when get the drug weights
                    drug_weights = select_drug_quantity(item['def.name'], info, defendants)
                else:
                    drug_weights = info['drug.weight']
                if info['doc'] == '12059051-9d92-4ac0-97eb-ed53ac3fb0fb.html':
                    print(item['def.name'])
                    print(info['crime'])
                    print(drug_weights)
                    # it can be improved by adding name information when in drug weights => a little complex
                drug_quantity_dict = get_drug_quantity(info['drug.type'], drug_weights, info['crime'])
                for drug_type in info['drug.type']:
                    if drug_type in drug_dict:
                        if len(drug_quantity_dict[drug_type]) > 0 and drug_quantity_dict[drug_type][-1] == "余":
                            drug_quantity_dict[drug_type] += "克"
                        item['drug.' + drug_dict[drug_type] + '.quantity'] = drug_quantity_dict[drug_type]
                    else:
                        item['drug.other.quantity'] += drug_quantity_dict[drug_type]

            # get fix imprison length
            item['pun.fiximpris.length'] = '0'
            pattern = re.compile("有期徒刑([\u2e80-\u9fff]+)")
            month_dict = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9,
                          "十": 10, "十一": 11, "两": 2}
            for line in info['pun']:
                if item_num > 1 and item['def.name'] not in line:
                    continue
                #match = re.search(pattern, line)
                #if match is not None:
                match_string = pattern.findall(line)
                if len(match_string) > 0:
                    #time_line = match.group(1)
                    time_line = match_string[-1]
                    time_line = time_line.split('缓刑')[0]
                    month_line = time_line
                    year = 0
                    if "年" in time_line:
                        year_index = time_line.index("年")
                        if time_line[year_index - 1] != "月":
                            year = time_line[:year_index]
                            #print(time_line)
                            #print(year)
                            year = getResultForDigit(year)
                            month_line = time_line[year_index+1:]
                        else:
                            month_line = time_line[:year_index-1]
                    month = 0
                    for number in month_dict.keys():
                        if number in month_line:
                            month = month_dict[number]
                    item['pun.fiximpris.length'] = str(month + year * 12)
            if item['pun.fiximpris.length'] == '0' and item_num > 1:
                for line in info['pun']:
                    if item['def.name'][0] in line:
                        match_string = pattern.findall(line)
                        if len(match_string) > 0:
                            # time_line = match.group(1)
                            time_line = match_string[-1]
                            month_line = time_line
                            year = 0
                            if "年" in time_line:
                                year_index = time_line.index("年")
                                if time_line[year_index - 1] != "月":
                                    year = time_line[:year_index]
                                    year = getResultForDigit(year)
                                    month_line = time_line[year_index + 1:]
                                else:
                                    month_line = time_line[:year_index - 1]
                            month = 0
                            for number in month_dict.keys():
                                if number in month_line:
                                    month = month_dict[number]
                            item['pun.fiximpris.length'] = str(month + year * 12)

            # get lifeimpris and death
            item['pun.lifeimpris'] = '0'
            item['pun.death'] = '0'
            if item_num == 1:
                for line in info['pun']:
                    if "无期徒刑" in line:
                        item['pun.lifeimpris'] = '1'
                    if "死刑" in line:
                        item['pun.death'] = '1'
            else:
                for line in info['pun']:
                    if item['def.name'] in line:
                        if "无期徒刑" in line:
                            item['pun.lifeimpris'] = '1'
                        if "死刑" in line:
                            item['pun.death'] = '1'

            # good attitude
            if 'def.goodattitude' in info:
                item['def.goodattitude'] = "1"
            else:
                item['def.goodattitude'] = "0"

            # recid
            if 'def.recid' in info:
                item['def.recid'] = info["def.recid"]
            else:
                item['def.recid'] = "0"

            # plead not guity
            if 'def.pleadnotguity' in info:
                item['def.pleadnotguity'] = info['def.pleadnotguity']

            # get crime types
            item['crime.drug.manufacture'] = "0"
            item['crime.drug.traffic'] = "0"
            item['crime.drug.smuggle'] = "0"
            item['crime.drug.transport'] = "0"
            item['crime.drug.possession'] = "0"
            if 'pun' in info:
                for punshiment in info['pun']:
                    if "制造" in punshiment:
                        item['crime.drug.manufacture'] = "1"
                    if "贩卖" in punshiment or "贩买" in punshiment:
                        item['crime.drug.traffic'] = "1"
                    if "走私" in punshiment:
                        item['crime.drug.smuggle'] = "1"
                    if "运输" in punshiment:
                        item['crime.drug.transport'] = "1"
                    if "持有" in punshiment:
                        item['crime.drug.possession'] = "1"

            # add item
            item_list.append(item)

        items[item['doc']] = item_list

    with open(items_path, 'w') as f:
        json.dump(items, f)


def run_get_items():
    # info_path = 'data/info.txt'
    # items_path = 'data/items.json'
    info_path = 'data/provinces/all_samples_info.txt'
    items_path = 'data/provinces/all_samples_items.json'
    get_items(info_path, items_path)


def evaluate(items_path, ref_file, res_file, errors_file):
    fout_error = open(errors_file, 'w')
    current_focus = ['doc',
                     'judge1.name', 'judge1.ethnic', 'judge2.name', 'judge2.ethnic', 'judge3.name', 'judge3.ethnic',
                     'def.name', 'def.name.prev', 'def.ethnicity', 'def.minority', 'def.recid', 'def.goodattitude', 'def.pleadnotguity',
                     'drug.opium', 'drug.opium.quantity', 'drug.heroin', 'drug.heroin.quantity', 'drug.marijuana',
                     'drug.marijuana.quantity', 'drug.meth', 'drug.meth.quantity', 'drug.cocaine',
                     'drug.cocaine.quantity', 'drug.other.name', 'drug.other.quantity',
                     'pun.fiximpris.length', 'pun.lifeimpris', 'pun.death', 'crime.drug.manufacture',
                     'crime.drug.traffic', 'crime.drug.smuggle', 'crime.drug.transport', 'crime.drug.possession']
    with open(items_path) as f:
        items = json.load(f)
    with open(ref_file) as f:
        ref_items = json.load(f)

    accuracy_dict = {}
    count_dict = {}
    pred_count = {}
    for key in current_focus[1:]:
        accuracy_dict[key] = 0
        count_dict[key] = 0
        pred_count[key] = 0
    fout = open(res_file, 'w')
    val_count = 0
    for key in items.keys():
        if key not in ref_items:
            continue
        for index in range(len(items[key])):
            item = items[key][index]
            ref_item = ref_items[key][index]
            val_count += 1
            correct_dict = {}
            for cur_key in accuracy_dict.keys():
                correct_dict[cur_key] = "wrong"
            for cur_key in accuracy_dict.keys():
                # add def minority for ref
                if cur_key == 'def.minority':
                    if ref_item['def.ethnicity'] == '汉族' or ref_item['def.ethnicity'] == "":
                        ref_item['def.minority'] = 0
                    else:
                        ref_item['def.minority'] = 1
                if cur_key == 'def.recid' and ref_item[cur_key] == "":
                    ref_item[cur_key] = "0"
                # change blank to 0 for recid
                if ref_item[cur_key] == item[cur_key]:
                    correct_dict[cur_key] = "correct"
                if item[cur_key] != '':
                    pred_count[cur_key] += 1
                if ref_item[cur_key] != '':
                    # revise the def prev name
                    if cur_key == 'def.name.prev':
                        def_name = ref_item[cur_key]
                        pattern = '(曾用名|别名|绰号|自称|别名|外号|经名|化名|又名|汉名|小名)([:：“])?([\u2e80-\u9fff]+)[,，)]?'
                        match = re.search(pattern, def_name)
                        if match is not None:
                            ref_item['def.name.prev'] = match.group(3)
                    count_dict[cur_key] += 1
                    if item[cur_key] == ref_item[cur_key]:
                        accuracy_dict[cur_key] += 1
                        correct_dict[cur_key] = 'correct'
                    #if "crime.drug." in cur_key and item[cur_key] != ref_item[cur_key]:
                        #fout_error.write(item['doc'] + "\n")
                        #fout_error.write(cur_key + "\n")
                        #fout_error.write('pred: ' + str(item[cur_key]) + "\n")
                        #fout_error.write('ref: ' + str(ref_item[cur_key]) + "\n")
                    #if "recid" in cur_key and item[cur_key] != ref_item[cur_key]:
                        #fout_error.write(item['doc'] + "\n")
                        #fout_error.write('pred: ' + str(item[cur_key]) + "\n")
                        #fout_error.write('ref: ' + str(ref_item[cur_key]) + "\n")

                    #if "goodattitude" in cur_key and item[cur_key] != ref_item[cur_key]:
                        #fout_error.write(item['doc'] + "\n")
                        #fout_error.write('pred: ' + str(item[cur_key]) + "\n")
                        #fout_error.write('ref: ' + str(ref_item[cur_key]) + "\n")
                if 'quantity' in cur_key and item[cur_key] != ref_item[cur_key]:
                    fout_error.write(item['doc'] + "\n")
                    fout_error.write(cur_key + "\n")
                    fout_error.write('pred: ' + str(item[cur_key]) + "\n")
                    fout_error.write('ref: ' + str(ref_item[cur_key]) + "\n")
                    #if (cur_key == 'pun.lifeimpris' or cur_key == "pun.death") and item[cur_key] != ref_item[cur_key]:
                        #if len(ref_item[cur_key]) != 0:
                            #fout_error.write(item['doc'] + "\n")
                            #fout_error.write(cur_key + '\n')
                            #fout_error.write('pred: ' + str(item[cur_key]) + "\n")
                            #fout_error.write('ref: ' + str(ref_item[cur_key]) + "\n")
                    #if cur_key == 'pun.fiximpris.length' and item[cur_key] != ref_item[cur_key]:
                        #if len(ref_item[cur_key]) != 0:
                            #fout_error.write(item['doc'] + "\n")
                            #fout_error.write('pred: ' + str(item[cur_key]) + "\n")
                            #fout_error.write('ref: ' + str(ref_item[cur_key]) + "\n")
                    #if 'drug' in cur_key and 'quantity' not in cur_key and item[cur_key] != ref_item[cur_key]:
                        #if str(item[cur_key]) != '1':
                        #fout_error.write(item['doc'] + "\n")
                        #fout_error.write('pred: ' + str(item[cur_key]) + "\n")
                        #fout_error.write('ref: ' + str(ref_item[cur_key]) + "\n")

                    #if cur_key == 'def.name.prev' and item[cur_key] != ref_item[cur_key]:
                        #fout_error.write(item['doc'] + "\n")
                        #fout_error.write('def name: ' + item['def.name'] + "\n")
                        #fout_error.write('ref def name: ' + ref_item['def.name'] + "\n")
                        #fout_error.write('pred: ' + item[cur_key] + "\n")
                        #fout_error.write('ref: ' + ref_item[cur_key] + "\n")
                    #elif cur_key == 'judge1.ethnic' or cur_key == 'judge2.ethnic' or cur_key == 'judge3.ethnic':
                        #print(item['doc'])
                    #print(ref_item[cur_key])
                    #if item['doc'] == '0189d39c-2879-4ad8-88f3-c59265ed5d0a.html':
                        #for char in item[cur_key]:
                            #print(char)
                            #print(hex(ord(char)))
            fout.write('doc: ' + item['doc'] + "\n")
            for cur_key in current_focus[1:]:
                fout.write(cur_key + ': ' + str(item[cur_key]) + " vs " + str(ref_item[cur_key]) + " " + correct_dict[cur_key]
                           + "\n")
            fout.write("\n")
    fout.write('---------------------------------------------------------------------------------------------------\n')
    fout.write('result\n')
    for key in current_focus[1:]:
        recall = 0.0
        precision = 0.0
        f1_score = 0.0
        if accuracy_dict[key] != 0:
            precision = accuracy_dict[key]/pred_count[key]
            recall = accuracy_dict[key]/count_dict[key]
        if precision + recall != 0:
            f1_score = 2 * precision * recall / (precision + recall)
        res_dict = {'precision': precision, 'recall': recall, 'f1_score': f1_score, 'correct num': accuracy_dict[key],
                    'pred num': pred_count[key], 'gold num': count_dict[key]}
        fout.write(key + ":\n")
        fout.write(str(res_dict) + "\n")
    fout.close()
    fout_error.close()


def run_evaluate():
    items_path = 'data/items.json'
    ref_file = 'data/xj_drug_2017.json'
    res_file = 'data/res.txt'
    errors_file = 'drug_quantity_errors.txt'
    evaluate(items_path, ref_file, res_file, errors_file)


def get_prediction(items_path, predict_path):
    current_focus = ['doc',
                     'judge1.name', 'judge1.ethnic', 'judge2.name', 'judge2.ethnic', 'judge3.name', 'judge3.ethnic',
                     'def.name', 'def.name.prev', 'def.ethnicity', 'def.minority', 'def.recid', 'def.goodattitude', 'def.pleadnotguity',
                     'drug.opium', 'drug.opium.quantity', 'drug.heroin', 'drug.heroin.quantity', 'drug.marijuana',
                     'drug.marijuana.quantity', 'drug.meth', 'drug.meth.quantity', 'drug.cocaine',
                     'drug.cocaine.quantity', 'drug.other.name', 'drug.other.quantity',
                     'pun.fiximpris.length', 'pun.lifeimpris', 'pun.death', 'crime.drug.manufacture',
                     'crime.drug.traffic', 'crime.drug.smuggle', 'crime.drug.transport', 'crime.drug.possession']
    contents = []
    with open(items_path) as f:
        items = json.load(f)
    for key in items.keys():
        for index in range(len(items[key])):
            item = items[key][index]
            contents.append([item[x] for x in current_focus])
    with open(predict_path, 'w') as f:
        writer = csv.writer(f)
        writer.writerow(current_focus)
        writer.writerows(contents)


def run_get_prediction():
    # items_path = 'data/items.json'
    # predict_path = 'data/xinjiang_drug_predicted_2017.csv'
    items_path = 'data/provinces/all_samples_items.json'
    predict_path = 'data/provinces/all_samples_predicted.csv'
    get_prediction(items_path, predict_path)


if __name__ == '__main__':
    # get_text()
    print('extract information')
    run_extract_information()
    print('get items')
    run_get_items()
    print('get prediction excel file')
    run_get_prediction()

    # print('evaluate')
    # run_evaluate()
