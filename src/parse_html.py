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

        info['def.name'] = lines[0]

        # initializes all the indices to 0
        
        info, idx_dict = find_indices(lines, info, drug_name)

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
        info = add_drug(info, drug_name)
        # if there is no 净重, we should add 克
        info = add_drug_weight(info, drug_name)
        info = add_drug_weight_from_lines_1(lines, info, drug_name)        
        # get crime if  without 审查查明 和 pun
        info = add_drug_weight_from_lines_2(lines, info, drug_name)
        
        # if there is no 净重, we should add 克 in all sentences
        info = add_drug_weight_from_all_sentences(lines, info)

        # find all judge names, juror names and secretary name
        temp_lines = lines[judge_index: secretary_index - 1]
        info, judge_name_list = add_judge_joror_names(temp_lines, info)
        info = add_ruling_date(lines, info, secretary_index)
        info = add_secretary(lines, info, secretary_index)

        # find all defendants' names
        temp_lines = lines[def_start: def_end]
        info = add_def_att_names(temp_lines, info)


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
    dir_path = '../data/corpus'
    info_path = '../data/info.txt'
    #dir_path = '../data/provinces/samples/all_drugs_samples'
    #info_path = '../data/provinces/all_samples_info.txt'
    extract_information(dir_path, info_path, DRUG_NAMES)





def get_def_name(info, nlp):
    names = []
    # get def name
    for item_index in range(len(info['def'])):
        item = {'def.name': ""}
        item = item_get_def_name(item, info, item_index)
        if item['def.name'] != "":
            names.append(item['def.name'])
    return names


def get_items(info_path, items_path, nlp_path=None, drug_dict=None, current_focus=None):
    if nlp_path is None:
        nlp = StanfordCoreNLP('/Users/zhengyuanxu/Programs/StanfordCoreNLP/stanford-corenlp-full-2018-10-05', lang='zh')

    if drug_dict is None:
        drug_dict = {"鸦片": 'opium', "海洛因": 'heroin', "大麻": 'marijuana', "兴奋剂": 'meth', "可卡因": 'cocaine',
                     "甲基苯丙胺": 'meth', "冰毒": 'meth', "甲基本丙胺": 'meth'}
    # "吗啡": 'morphia', "那可汀": 'narcotine', "摇头丸": 'MDMA', "古柯叶": 'coca leaves'
    if current_focus is None:
        current_focus = ['doc',
                         'judge1.name', 'judge1.ethnic', 'judge2.name', 'judge2.ethnic', 'judge3.name', 'judge3.ethnic',
                         'def.name', 'def.name.prev', 'def.ethnicity', 'def.recid', 'def.goodattitude', 'def.pleadnotguity',
                         'drug.opium', 'drug.opium.quantity', 'drug.heroin', 'drug.heroin.quantity', 'drug.marijuana',
                         'drug.marijuana.quantity', 'drug.meth', 'drug.meth.quantity', 'drug.cocaine',
                         'drug.cocaine.quantity', 'drug.other.name', 'drug.other.quantity',
                         'pun.fiximpris.length', 'pun.lifeimpris', 'pun.death', 'crime.drug.manufacture',
                         'crime.drug.traffic', 'crime.drug.smuggle', 'crime.drug.transport', 'crime.drug.possession']
    

                         
    info_list = read_info(info_path)
    
    items = {}
    doc_num = 0
    for info in info_list:
        doc_num += 1
        if 'def' not in info:
            item_num = 1
        else:
            item_num = len(info['def'])
        item_list = []

        # if item_num > 1:
        defendants = get_def_name(info, nlp)
        for item_index in range(item_num):
            item = {}
            for key in current_focus:
                item[key] = ""
            for key in info.keys():
                if key in current_focus:
                    item[key] = info[key]

            # get judge ethnic
            item = get_judge_ethnic(item)

            # get def name
            item = item_get_def_name(item, info, item_index)

            # get def ethnic
            item = get_def_ethnic(item, info, item_index)

            # add def minority
            item = get_def_minority(item)

            # get def previous name
            item = get_def_previous_name(item, info, item_index)

            # get drug type
            item = get_drug_type(item, info, drug_dict)

            # get drug quantity
            item = item_get_drug_quantity(item, info, defendants, drug_dict, item_num)


            # get fix imprison length
            item = get_fix_imprison_length(item, info, item_num)

            # get lifeimpris and death
            item = get_lifeimpris_and_death(item, info, item_num)


            # good attitude
            item = get_good_attitude(item, info)

            # recid
            item = get_recid(item, info)

            # plead not guity
            item = get_plead_not_guilty(item, info)

            # get crime types
            item = get_crime_types(item, info)

            # add item
            item_list.append(item)

        items[item['doc']] = item_list

    with open(items_path, 'w') as f:
        json.dump(items, f)

    nlp.close()


def run_get_items():
    # info_path = 'data/info.txt'
    # items_path = 'data/items.json'
    info_path = '../data/provinces/all_samples_info.txt'
    items_path = '../data/provinces/all_samples_items.json'
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
    items_path = '../data/items.json'
    ref_file = '../data/xj_drug_2017.json'
    res_file = '../data/res.txt'
    errors_file = '../errors/drug_quantity_errors.txt'
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
    items_path = '../data/provinces/all_samples_items.json'
    predict_path = '../data/provinces/all_samples_predicted.csv'
    get_prediction(items_path, predict_path)


if __name__ == '__main__':
    # get_text('xj_drugs')
    print('extract information')
    run_extract_information()
    print('get items')
    run_get_items()
    print('get prediction excel file')
    run_get_prediction()

    # print('evaluate')
    # run_evaluate()
