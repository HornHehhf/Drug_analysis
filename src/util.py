'''
Function names:
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


def find_def_idx(line, idx_dict):
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

def find_info(line, info):
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

def find_pun(line, idx_dict, raw_line):
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
def find_indices(lines, info, idx_dict=None):
    if idx_dict is None:
        idx_dict = {
        'pun_start': 0,
        'pun_end': 0,
        'judge_index': 0,
        'secretary_index': 0,
        'def_start': 0,
        'def_end': 0
        }

    for index in range(len(lines))[6:]:
        line = lines[index]
        raw_line = "".join(line.split('\u3000'))
        raw_line = "".join(raw_line.split(' '))

        '''if "独任审判":
            if "独任审判" not in info['trial.phase']:
                info['trial.phase'] = info['trial.phase'] + "独任审判"'''

        # find indices of sentences containing 被告姓名
        idx_dict = find_def_idx(line, idx_dict)
        info = find_info(line, info)
        idx_dict = find_pun(line, idx_dict, raw_line)

    return info, idx_dict

def add_pun(lines, info):
    for line in lines:
        if line[0] == '（':
            pattern = "[0-9]*年[0-9]*月[0-9]*日"
            match = re.search(pattern, line)
            if match is not None:
                info['execution.date'] = match.group()
            continue
        if line not in info['pun'] and line[0] != '（':
            info['pun'].append(line)

    return info

def add_drug(info):
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

def add_drug_weight(info):
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

def add_drug_weight_from_lines_1(lines, info):
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

def add_drug_weight_from_lines_2(lines, info):
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

def add_ruling_date(lines, info):
    info['ruling.date'] = lines[secretary_index - 1]
    return info

def add_secretary(lines, info)
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