#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import json


def get_ref(csv_file, ref_file):
    current_focus = ['judge1.name', 'judge1.ethnic', 'judge2.name', 'judge2.ethnic', 'judge3.name', 'judge3.ethnic',
                     'def.name', 'def.name.prev', 'def.ethnicity', 'def.recid', 'def.goodattitude', 'def.pleadnotguity',
                     'drug.opium', 'drug.opium.quantity', 'drug.heroin', 'drug.heroin.quantity', 'drug.marijuana',
                     'drug.marijuana.quantity', 'drug.meth', 'drug.meth.quantity', 'drug.cocaine',
                     'drug.cocaine.quantity', 'drug.other.name', 'drug.other.quantity',
                     'pun.fiximpris.length', 'pun.lifeimpris', 'pun.death', 'doc', 'crime.drug.manufacture',
                     'crime.drug.traffic', 'crime.drug.smuggle', 'crime.drug.transport', 'crime.drug.possession']
    content = []
    with open(csv_file) as f:
        reader = csv.reader(f)
        for row in reader:
            content.append(row)
    print(content[0])
    key_dict = {}
    for index in range(len(content[0])):
        key_dict[index] = content[0][index]
    items = {}
    last_doc = ""
    for index in range(len(content))[1:]:
        item = content[index]
        item_dict = {}
        for j in range(len(item)):
            if key_dict[j] in current_focus:
                item_dict[key_dict[j]] = item[j]
        if item_dict['doc'] == "":
            item_dict['doc'] = last_doc
        if item_dict['doc'] in items:
            items[item_dict['doc']].append(item_dict)
        else:
            items[item_dict['doc']] = [item_dict]
        if item_dict['doc'] != "":
            last_doc = item_dict['doc']
    with open(ref_file, 'w') as f:
        json.dump(items, f)


if __name__ == '__main__':
    csv_file = 'data/xinjiang_drug_allcoded_2017.csv'
    ref_file = 'data/xj_drug_2017.json'
    get_ref(csv_file, ref_file)
