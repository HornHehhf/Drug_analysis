
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
