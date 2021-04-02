def load_translation_dict(translation_file = "45983a_fr_simple_mt_tr_2.fw_ttable1"):
i
    lines = open(translation_file).readlines()
    for line in lines:
        line_splitted = line.split()
        fr = line_splitted[0]
        en = line_splitted[1]
        prob = float(line_splitted[2])
        translation_dict.setdefault(fr, [])
        translation_dict[fr].append((en,prob))

def get_translation(fr):
    return translation_dict[fr]


translation_dict = {}   
load_translation_dict()
print(get_translation("surviendraient"))
        
