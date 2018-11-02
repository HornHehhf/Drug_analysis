'''
***Function names***
(for extract_information in parsing.py)
find_def_idx
find_info
find_pun
find_indices
add_pun
add_drug
add_drug_weight
add_drug_weight_from_lines_1
add_drug_weight_from_lines_2
add_drug_weight_from_all_sentences
add_judge_joror_names
add_def_att_names
add_ruling_date
add_secretary
add_attitude

'''
import re

def find_def_idx(line, idx_dict, index, lines):
    if "被告人" == line[0:3] or line[0:3] == "辩护人":
        if idx_dict['def_start'] == 0:
            idx_dict['def_start'] = index
        if index + 1 > len(lines) - 1:
            if idx_dict['def_end'] == 0:
                idx_dict['def_end'] = index + 1
        elif lines[index+1][0:3] != "被告人" and lines[index+1][0:3] != "辩护人":
            if idx_dict['def_end'] == 0:
                idx_dict['def_end'] = index + 1
    return idx_dict

def find_info(line, info, index, drug_name):
    if "经审理查明" in line and "经审理查明：" != line:
        pattern = "[0-9]*年[0-9]*月[0-9]*日"
        match = re.search(pattern, line)
        if match is not None:
            info['crime.date'] = match.group()  # multiple time may cause error
        info['drug.type'] = []
        for name in drug_name:
            if name in line:
                info['drug.type'].append(name)
        #match = re.search(pattern, line)
        #if match is not None:
            #info['drug.weight'].append(match.group())
    return info

def find_pun(line, idx_dict, raw_line, index):
    if "判决如下" in line:
        idx_dict['pun_start'] = index + 1
    elif "如不服本判决" in line:
        idx_dict['pun_end'] = index
    elif ("审判长" in raw_line or "审判员" in raw_line) and len(raw_line) < 15:
        if idx_dict['judge_index'] == 0:
            idx_dict['judge_index'] = index
    elif "书　记　员" in line:
        idx_dict['secretary_index'] = index

    return idx_dict
'''
return a dict containing indices of relevant sentences
indices:
pun_start: starting sentence of 判决
pun_end: ending sentence of 判决
judge_index: 审判长 or 审判员
secretary_index: 书记员
def_start: starting sentence of 被告
def_end: ending sentence of 被告
'''
def find_indices(lines, info, drug_name, idx_dict=None):
    if idx_dict is None:
        idx_dict = {
        'pun_start': 0,
        'pun_end': 0,
        'judge_index': 0,
        'secretary_index': 0,
        'def_start': 0,
        'def_end': 0
        }
    length = len(lines)
    for index in range(len(lines))[6:]:
        line = lines[index]
        raw_line = "".join(line.split('\u3000'))
        raw_line = "".join(raw_line.split(' '))

        '''if "独任审判":
            if "独任审判" not in info['trial.phase']:
                info['trial.phase'] = info['trial.phase'] + "独任审判"'''

        # find indices of sentences containing 被告姓名

        idx_dict = find_def_idx(line, idx_dict, index, lines)
        info = find_info(line, info, index, drug_name)
        idx_dict = find_pun(line, idx_dict, raw_line, index)

    return info, idx_dict

def add_pun(lines, info):
    for line in lines:
        if line:
            if line[0] == '（':
                pattern = "[0-9]*年[0-9]*月[0-9]*日"
                match = re.search(pattern, line)
                if match is not None:
                    info['execution.date'] = match.group()
                continue
            if line not in info['pun'] and line[0] != '（':
                info['pun'].append(line)

    return info

def add_drug(info, drug_name):
    if 'drug.type' not in info:
        info['drug.type'] = []
    for line in info['pun']:
        add_line = False
        for name in drug_name:
            if name in line:
                if name not in info['drug.type']:
                    add_line = True
                    info['drug.type'].append(name)
                pattern = re.compile(r'净重[为是达]*([0-9]+\.?[0-9]*[余]*)[克可]')
                tmp_weights = pattern.findall(line)
                if 'drug.weight' not in info:
                    info['drug.weight'] = []
                for weight in tmp_weights:
                    if weight not in info['drug.weight']:
                        info['drug.weight'].append(weight)
                        add_line = True
        if add_line:
            if 'crime' not in info or len(info['crime']) == 0:
                info['crime'] = line
            else:
                info['crime'] = info['crime'] + '\t'*100 + line
    return info

def add_drug_weight(info, drug_name):
    if 'drug.weight' not in info or len(info['drug.weight']) == 0:
        for line in info['pun']:
            add_line = False
            for name in drug_name:
                if name in line:
                    pattern = re.compile(r'([0-9]+\.?[0-9]*[余]*)[克可]')
                    tmp_weights = pattern.findall(line)
                    if 'drug.weight' not in info:
                        info['drug.weight'] = []
                    for weight in tmp_weights:
                        if weight not in info['drug.weight']:
                            info['drug.weight'].append(weight)
                            add_line = True
            if add_line:
                if 'crime' not in info or len(info['crime']) == 0:
                    info['crime'] = line
                else:
                    info['crime'] = info['crime'] + '\t'*100 + line
    return info

def add_drug_weight_from_lines_1(lines, info, drug_name):
    if 'crime' not in info:
        for index in range(len(lines))[6:]:
            line = lines[index]
            add_line = False
            if "经审理查明" in line or "经审理查明：" in line or "本院认为" in line:
                pattern = "[0-9]*年[0-9]*月[0-9]*日"
                match = re.search(pattern, line)
                if match is not None:
                    info['crime.date'] = match.group()  # multiple time may cause error
                for name in drug_name:
                    if name in line and name not in info['drug.type']:
                        info['drug.type'].append(name)
                info['drug.weight'] = []
                pattern = re.compile(r'净重[为是达]*([0-9]+\.?[0-9]*[余]*)[克可]')  # improve
                tmp_weights = pattern.findall(line)
                if 'drug.weight' not in info:
                    info['drug.weight'] = []
                for weight in tmp_weights:
                    if weight not in info['drug.weight']:
                        info['drug.weight'].append(weight)
                        add_line = True
            if add_line:
                if 'crime' not in info or len(info['crime']) == 0:
                    info['crime'] = line
                else:
                    info['crime'] = info['crime'] + '\t' * 100 + line
    return info

def add_drug_weight_from_lines_2(lines, info, drug_name):
    if 'crime' not in info:
        for index in range(len(lines))[6:]:
            line = lines[index]
            add_line = False
            if "公诉机关指控，" in line or "检察院指控，" in line or "公诉机关指控：" in line[:-10] \
                    or "检察院指控：" in line[:-10] or "公诉机关指控：" == lines[index-1][-7:] \
                    or "检察院指控：" == lines[index-1][-6:] or "经审理查明：" == lines[index-1]:
                pattern = "[0-9]*年[0-9]*月[0-9]*日"
                match = re.search(pattern, line)
                if match is not None:
                    info['crime.date'] = match.group()  # multiple time may cause error
                for name in drug_name:
                    if name in line and name not in info['drug.type']:
                        info['drug.type'].append(name)
                info['drug.weight'] = []
                pattern = re.compile(r'净重[为是达]*([0-9]+\.?[0-9]*[余]*)[克可]')  #improve
                tmp_weights = pattern.findall(line)
                if 'drug.weight' not in info:
                    info['drug.weight'] = []
                for weight in tmp_weights:
                    if weight not in info['drug.weight']:
                        info['drug.weight'].append(weight)
                        add_line = True
            if add_line:
                if 'crime' not in info or len(info['crime']) == 0:
                    info['crime'] = line
                else:
                    info['crime'] = info['crime'] + '\t'*100 + line
    return info

def add_drug_weight_from_all_sentences(lines, info):
    if 'drug.weight' not in info or len(info['drug.weight']) == 0:
        info['drug.weight'] = []
        if 'crime' not in info:
            info['crime'] = []
        for index in range(len(lines))[6:]:
            line = lines[index]
            #if "公诉机关指控，" in line or "检察院指控，" in line or "公诉机关指控：" in line[:-10] \
                    #or "检察院指控：" in line[:-10] or "公诉机关指控：" == lines[index-1][-7:] \
                    #or "检察院指控：" == lines[index-1][-6:] or "经审理查明：" == lines[index-1]:
            if True:
                add_line = False
                pattern = re.compile(r'([0-9]+\.?[0-9]*[余]*)[克可]')  #improve
                tmp_weights = pattern.findall(line)
                if 'drug.weight' not in info:
                    info['drug.weight'] = []
                for weight in tmp_weights:
                    if weight not in info['drug.weight']:
                        info['drug.weight'].append(weight)
                        add_line = True
                if add_line:
                    if 'crime' not in info or len(info['crime']) == 0:
                        info['crime'] = line
                    else:
                        info['crime'] = info['crime'] + '\t' * 100 + line
    return info

def add_judge_joror_names(lines, info):
    judge_name_list = []
    for line in lines:
        raw_line = "".join(line.split('\u3000'))
        raw_line = "".join(raw_line.split(' '))
        raw_line = "".join(raw_line.split(':'))
        raw_line = "".join(raw_line.split('：'))
        if "审判长" in raw_line:
            index = raw_line.index("审判长")
            judge_name_list.append(raw_line[index+3:])
        if "审判员" in raw_line:
            index = raw_line.index("审判员")
            judge_name_list.append(raw_line[index+3:])
        if "人民陪审员" in line:
            if 'juror.name' in info:
                info['juror.name'].append("".join(line.split('\u3000'))[5:])
            else:
                info['juror.name'] = ["".join(line.split('\u3000'))[5:]]

    return info, judge_name_list

def add_def_att_names(lines, info):
    for line in lines:
        if line[0:3] == "被告人":
            if 'def' in info:
                info['def'].append(line.split('。')[0])
            else:
                info['def'] = [line.split('。')[0]]
        if line[0:3] == "辩护人":
            if 'attorney' in info:
                info['attorney'].append(line.split('。')[0])
            else:
                info['attorney'] = [line.split('。')[0]]

    return info

def add_ruling_date(lines, info, secretary_index):
    info['ruling.date'] = lines[secretary_index - 1]
    return info

def add_secretary(lines, info, secretary_index):
    info['secretary.name'] = "".join(lines[secretary_index].split("\u3000"))[3:]
    return info

def add_attitude(lines, info):
    for index in range(len(lines))[6:]:
        # good attitude
        line = lines[index]
        if "认罪态度良好" in line or "认罪态度较好" in line or "认罪态度好" in line or "无异议" in line \
                or "不持异议" in line or "没有异议" in line or "自愿认罪" in line \
                or "如实供述" in line or "自首" in line:
            info['def.goodattitude'] = "1"

         # recid
        if "累犯" in line or "再犯" in line or "再次犯" in line or "再次进行毒品犯罪" in line \
                or "再次进行犯罪" in line or ("有前科" in line and "没有前科" not in line) \
                or ("有犯罪前科" in line and "没有犯罪前科" not in line) or "又犯" in line \
                or "曾犯" in line or "曾因毒品犯罪" in line or "判处过" in line or "不思悔改" in line\
                or "曾因犯" in line:
            info['def.recid'] = "1"
        elif "初犯" in line:
            info['def.recid'] = "0"

        # plead not guity
        if "不认罪" in line or "认罪态度差" in line \
                or "认罪态度较差" in line or "认罪态度极差" in line:
            info['def.pleadnotguity'] = "1"
            if "def.goodattitude" in info and info['def.goodattitude'] == "1":
                info['def.pleadnotguity'] = ""
    return info


##################################################################################################


'''
***Function names***
(for get_items in parsing.py)
read_info
get_judge_ethnic
item_get_def_name
get_def_ethnic
get_def_minority
get_def_previous_name
get_drug_type
get_type_quantity_distance
get_drug_quantity
select_drug_quantity
item_get_drug_quantity
get_fix_imprison_length
get_lifeimpris_and_death
get_good_attitude
get_recid
get_plead_not_guilty
get_crime_types
'''

def read_info(info_path):
    fin = open(info_path)
    lines = fin.readlines()
    lines = [line.strip() for line in lines]
    fin.close()
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

    return info_list


def get_judge_ethnic(item):
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

    return item

def item_get_def_name(item, info, item_index):
    if 'def' in info:
        def_name = info['def'][item_index] + "\n"
        pattern = '被告人[：]?([\u2e80-\u9fffxX×＊·ⅹ.*]+)[0-9（，\n,( \uff3b犯]'
        match = re.search(pattern, def_name)
        if match is not None:
            item['def.name'] = match.group(1)
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
                words = nlp.ner(info['def.name'])
                ner_def_names = []
                for word_tuple in words:
                    if word_tuple[1] == "PERSON":
                        ner_def_names.append(word_tuple[0])
                if item_index < len(ner_def_names):
                    item['def.name'] = ner_def_names[item_index]
                else:
                    # error caused by fan
                    fan_index = info['def.name'].find('犯')
                    if fan_index != -1:
                        item['def.name'] = info['def.name'][:fan_index]
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
        words = nlp.ner(info['def.name'])
        ner_def_names = []
        for word_tuple in words:
            if word_tuple[1] == "PERSON":
                ner_def_names.append(word_tuple[0])
        if len(ner_def_names) != 0:
            item['def.name'] = ner_def_names[item_index]
        # error caused by fan
        if "犯" in item['def.name']:
            item['def.name'] = item['def.name'].split("犯")[0]
        if info['doc'] == '3538c56f-c136-4ba5-8d6d-b195bc5c16dc.html':
            print(item['def.name'])
        else:
            fan_index = info['def.name'].find('犯')
            if fan_index != -1:
                item['def.name'] = info['def.name'][:fan_index]
    return item

def get_def_ethnic(item, info, item_index):
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

    return item


def get_def_minority(item):
    if item['def.ethnicity'] == '汉族':
        item['def.minority'] = 0
    else:
        item['def.minority'] = 1

def get_def_previous_name(item, info, item_index):
    if 'def' in info:
        def_name = info['def'][item_index] + "\n"
        pattern = '(曾用名|别名|绰号|自称|别名|外号|经名|化名|又名|汉名|小名)([:：“])?([\u2e80-\u9fff]+)[,，)]?'
        match = re.search(pattern, def_name)
        if match is not None:
            if item['def.name.prev'] != "":
                item['def.name.prev'] = item['def.name.prev'] + '、' + match.group(3)
            else:
                item['def.name.prev'] = match.group(3)
    return item

def get_drug_type(item, info, drug_dict):
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

    return item


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

def item_get_drug_quantity(item, info, defendants, drug_dict):
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

    return item


def get_fix_imprison_length(item, info):
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

    return item


def get_lifeimpris_and_death(item, info):
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

    return item

def get_good_attitude(item, info):
    if 'def.goodattitude' in info:
        item['def.goodattitude'] = "1"
    else:
        item['def.goodattitude'] = "0"

    return item

def get_recid(item, info):
    if 'def.pleadnotguity' in info:
        item['def.pleadnotguity'] = info['def.pleadnotguity']

    return item

def get_plead_not_guilty(item, info):
    if 'def.pleadnotguity' in info:
        item['def.pleadnotguity'] = info['def.pleadnotguity']

    return item

def get_crime_types(item, info):
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

    return item