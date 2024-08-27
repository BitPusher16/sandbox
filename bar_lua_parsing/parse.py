import luadata
import os
from os.path import expanduser

import json

home = expanduser('~')
#bar_dir = os.path.join(home, '/src/Beyond-All-Reason') # os.path.join doesn't like '/' char.
bar_dir = os.path.join(home, 'src/Beyond-All-Reason/units')
#print(home)
#print(bar_dir)

for f in os.listdir(bar_dir):
    if f.endswith('.lua'):
        pass
        #print(f)

units = {}
for root, d_names, f_names in os.walk(bar_dir):
    #print(root, d_names, f_names)
    for f_name in f_names:
        if(f_name.endswith('.lua')):
            #print(f_name)
            f_path = os.path.join(root, f_name)
            #print(f_path)
            unit_name = f_name.replace('.lua', '')
            try:
                units[unit_name] = luadata.read(f_path, encoding="utf-8")[unit_name]
            except:
                pass

#print(units)
#print(units['corcomcon'])

f_out = os.path.join(home, 'dat/tmp/bar_units.json')
with open(f_out, 'w', encoding='utf-8') as f:
    json.dump(units, f, ensure_ascii=False, indent=4)
