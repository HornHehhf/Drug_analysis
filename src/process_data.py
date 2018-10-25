import os
from os import listdir
import shutil
import numpy as np


def mkdir(path):
    folder = os.path.exists(path)

    if not folder:
        os.makedirs(path)


def split_province():
    folders = ['ah_drugs', 'bj_drugs', 'cq_drugs', 'fj_drugs', 'gd_drugs', 'gs_drugs', 'gx_drugs', 'gz_drugs',
               'ha_drugs', 'hb_drugs', 'he_drugs', 'hi_drugs', 'hk_drugs', 'hl_drugs', 'hn_drugs', 'jl_drugs',
               'js_drugs', 'jx_drugs', 'ln_drugs', 'mo_drugs', 'nm_drugs', 'nx_drugs', 'qh_drugs', 'sc_drugs',
               'sd_drugs', 'sh_drugs', 'sn_drugs', 'sx_drugs', 'tj_drugs', 'tw_drugs', 'xj_drugs', 'xz_drugs',
               'yn_drugs', 'zj_drugs', 'not_drugs', 'unclear_drugs']
    province_names = {'湖南': 'hn', '湖北': 'hb', '广东': 'gd', '广西': 'gx', '河南': 'ha', '河北': 'he', '山东': 'sd',
                      '山西': 'sx', '澳门': 'mo', '香港': 'hk', '西藏': 'xz', '台湾': 'tw', '贵州': 'gz', '云南': 'yn',
                      '四川': 'sc', '北京': 'bj', '上海': 'sh', '天津': 'tj', '重庆': 'cq', '宁夏': 'nx', '辽宁': 'ln',
                      '甘肃': 'gs', '青海': 'qh', '陕西': 'sn', '海南': 'hi', '内蒙古': 'nm', '江苏': 'js', '江西': 'jx',
                      '浙江': 'zj', '黑龙江': 'hl', '新疆': 'xj', '福建': 'fj', '吉林': 'jl', '安徽': 'ah'}

    province_city = {'hn': ['长沙、株洲、湘潭、衡阳、邵阳、岳阳、常德、张家界、益阳、郴州、永州、怀化、娄底', '湘西'],
                     'hb': ['武汉、鄂州、黄冈、孝感、黄石、咸宁、荆门、宜昌、荆州、襄阳、随州、十堰', '恩施'],
                     'gd': ['广州、深圳、佛山、东莞、中山、珠海、江门、肇庆、惠州、汕头、潮州、揭阳、汕尾、湛江、茂名、阳江、韶关、清远、云浮、梅州、河源'],
                     'gx': ['南宁', '柳州', '桂林', '梧州', '北海', '防城港', '钦州', '贵港', '玉林', '百色', '贺州', '河池',
                            '来宾', '崇左'],
                     'ha': ['郑州', '开封', '洛阳', '平顶山', '安阳', '鹤壁', '新乡', '焦作', '濮阳', '许昌', '漯河', '三门峡',
                            '商丘', '周口', '驻马店', '南阳', '信阳', '济源'],
                     'he': ['石家庄', '唐山', '秦皇岛', '邯郸', '邢台', '保定', '张家口', '承德', '沧州', '廊坊', '衡水'],
                     'sd': ['济南', '青岛', '淄博', '枣庄', '东营', '烟台', '潍坊', '济宁', '泰安', '威海', '日照', '滨州',
                            '德州', '聊城', '临沂', '菏泽', '莱芜'],
                     'sx': ['大同、朔州、忻州、阳泉、吕梁、晋中、长治、晋城、临汾、运城', '太原'],
                     'mo': ['花地玛', '圣安多尼', '大堂', '望德', '风顺', '嘉模', '圣方济各', '路氹'],
                     'hk': ['中西区、湾仔、东区、南区', '油尖旺、深水埗、九龙城、黄大仙、观塘', '北区、大埔、沙田、西贡、荃湾、屯门、元朗、葵青、离岛'],
                     'xz': ['拉萨', '那曲', '昌都', '山南', '阿里', '日喀则', '林芝'],
                     # 'tw': ['台北', '新北', '桃园', '台中', '台南', '高雄', '基隆', '新竹', '嘉义', '新竹'],
                     'gz': ['贵阳', '遵义', '六盘水', '安顺', '毕节', '铜仁', '黔东南', '黔南'],
                     'yn': ['昆明', '曲靖', '玉溪', '昭通', '保山', '丽江', '普洱', '临沧', '德宏', '怒江', '迪庆', '大理',
                            '楚雄', '红河', '文山', '西双版纳'],
                     'sc': ['成都', '绵阳', '自贡', '攀枝花', '泸州', '德阳', '广元', '遂宁', '内江', '乐山', '资阳', '宜宾',
                            '南充', '达州', '雅安', '阿坝', '甘孜', '凉山', '广安', '巴中', '眉山'],
                     'bj': ['东城、西城、朝阳、丰台、石景山、海淀、顺义、通州、大兴、房山、门头沟、昌平、平谷、密云、怀柔、延庆'],
                     'sh': ['黄浦', '徐汇', '长宁', '静安', '普陀', '虹口', '杨浦', '浦东', '闵行', '宝山', '嘉定', '金山',
                            '松江', '青浦', '奉贤', '崇明'],
                     'tj': ['和平', '河东', '河西', '南开', '河北', '红桥', '滨海', '东丽', '西青', '津南', '北辰', '武清',
                            '宝坻', '宁河', '静海', '蓟州'],
                     'cq': ['渝中', '万州', '涪陵', '大渡口', '江北', '沙坪坝', '九龙坡', '南岸', '北碚', '綦江', '大足',
                            '渝北', '巴南', '黔江', '长寿', '江津', '合川', '永川', '南川', '璧山', '铜梁', '潼南', '荣昌',
                            '开州', '梁平', '武隆', '城口', '丰都', '垫江', '忠县', '云阳', '奉节', '巫山', '巫溪', '石柱',
                            '秀山', '酉阳', '彭水'],
                     'nx': ['银川', '石嘴山', '吴忠', '固原', '中卫'],
                     'ln': ['沈阳', '大连', '鞍山', '抚顺', '本溪', '丹东', '锦州', '营口', '阜新', '辽阳', '盘锦', '铁岭',
                            '朝阳市', '葫芦岛'],
                     'gs': ['兰州', '嘉峪关', '金昌', '白银', '天水', '武威', '张掖', '平凉', '酒泉', '庆阳', '定西', '陇南',
                            '临夏', '甘南'],
                     'qh': ['西宁', '海东', '海北', '黄南', '海南', '果洛', '玉树', '海西'],
                     'sn': ['西安', '宝鸡', '咸阳', '铜川', '渭南', '延安', '榆林', '汉中', '安康', '商洛'],
                     'hi': ['海口', '三亚', '三沙', '儋州', '洋浦'],
                     'nm': ['呼和浩特', '包头', '乌海', '赤峰', '通辽', '鄂尔多斯', '呼伦贝尔', '巴彦淖尔', '乌兰察布', '兴安',
                            '锡林郭勒', '阿拉善'],
                     'js': ['南京', '无锡', '徐州', '常州', '苏州', '南通', '连云港', '淮安', '盐城', '扬州', '镇江', '泰州',
                            '宿迁'],
                     'jx': ['南昌', '九江', '上饶', '抚州', '宜春', '吉安', '赣州', '景德镇', '萍乡', '新余', '鹰潭'],
                     'zj': ['杭州', '宁波', '温州', '绍兴', '湖州', '嘉兴', '金华', '衢州', '台州', '丽水', '舟山'],
                     'hl': ['哈尔滨', '齐齐哈尔', '牡丹江', '佳木斯', '大庆', '鸡西', '双鸭山', '伊春', '七台河', '鹤岗',
                            '黑河', '绥化', '大兴安岭'],
                     'xj': ['乌鲁木齐', '克拉玛依', '吐鲁番', '哈密', '阿克苏', '喀什', '和田', '昌吉', '博尔塔拉', '巴音郭楞',
                            '克孜勒苏', '伊犁', '塔城', '阿勒泰'],
                     'fj': ['福州', '厦门', '漳州', '泉州', '三明', '莆田', '南平', '龙岩', '宁德', '平潭'],
                     'jl': ['长春', '吉林', '四平', '辽源', '通化', '白山', '白城', '松原', '延边'],
                     'ah': ['宿州、淮北、亳州、阜阳、蚌埠、淮南、滁州、六安、马鞍山、安庆、芜湖、铜陵、宣城、池州、黄山']}
    city_names = {}

    # get city names
    for key, value in province_city.items():
        print(key)
        print(value)
        for sent in value:
            if '、' in sent:
                words = sent.split('、')
                for word in words:
                    city_names[word] = key
            else:
                city_names[sent] = key

    print(city_names)
    # print(province_names)

    for fold in folders:
        mkdir('../provinces/' + fold)

    dir_path = '../DrugResult'
    files = listdir(dir_path)
    file_num = 0
    for file in files:
        file_num += 1
        print(file_num, end='\r')
        # print(file)
        tmp_file = dir_path + '/' + file
        fin = open(tmp_file, errors='ignore')
        fin.readline()
        fin.readline()
        line_province = fin.readline()
        # lines = fin.readlines()
        # if len(lines) < 3:
            # continue
        # line_province = lines[2]
        # drug_flag = False
        # if "毒品" not in line_drug:
            # check in xj province to judge drug cases
            # shutil.copyfile(tmp_file, 'data/not_drugs/' + file)
        # else:
        province_dir = 'unclear'
        for key in province_names:
            if key in line_province:
                province_dir = province_names[key]
                break
        if province_dir == 'unclear':
            for key in city_names:
                if key in line_province:
                    province_dir = city_names[key]

        '''line = "".join(lines)
        # pun_index = line.index("判决如下")
        if "毒品" in line:
            drug_flag = True
        if not drug_flag:
            province_dir = 'not'''''

        shutil.copyfile(tmp_file, '../provinces/' + province_dir + '_drugs/' + file)


def get_sample_data():
    mkdir('../provinces/samples')
    mkdir('../provinces/samples/yn_drugs_samples')
    mkdir('../provinces/samples/gd_drugs_samples')
    mkdir('../provinces/samples/all_drugs_samples')
    mkdir('../provinces')
    yn_drugs = listdir('../provinces/yn_drugs')
    np.random.shuffle(yn_drugs)
    gd_drugs = listdir('../provinces/gd_drugs')
    np.random.shuffle(gd_drugs)
    all_drugs = listdir('../Result')
    np.random.shuffle(all_drugs)
    for file in yn_drugs[:150]:
        shutil.copy('../provinces/yn_drugs/' + file, '../provinces/samples/yn_drugs_samples/' + file)
    for file in gd_drugs[:150]:
        shutil.copy('../provinces/gd_drugs/' + file, '../provinces/samples/gd_drugs_samples/' + file)
    for file in all_drugs[:300]:
        shutil.copy('../Result/' + file, '../provinces/samples/all_drugs_samples/' + file)


def analyze_xj():
    original_dir = 'data/corpus'
    new_dir = '../provinces/xj_drugs'
    original_files = list(set(listdir(original_dir)))
    new_files = list(set(listdir(new_dir)))
    matched_num = 0
    for file in original_files:
        if file in new_files:
            matched_num += 1
    print('original file num (xj): ', len(original_files))
    print('new file num (xj): ', len(new_files))
    print('matched file num (xj): ', matched_num)


if __name__ == '__main__':
    # split_province()
    # get_sample_data()
    analyze_xj()
