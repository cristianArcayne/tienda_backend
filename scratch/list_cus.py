import os
import glob
import re

for f in sorted(glob.glob('routers/*.py')):
    if f.endswith('__init__.py'):
        continue
    with open(f, 'r', encoding='utf-8', errors='ignore') as file_obj:
        content = file_obj.read()
        tags = re.findall(r'tags=\[([^\]]+)\]', content)
        doc = ""
        lines = content.split('\n')
        for line in lines[:10]:
            if "CU" in line or "Router" in line or "Caso" in line or "tags" in line:
                doc += line.strip() + " "
        print(f"{os.path.basename(f)}: {tags} | {doc[:80]}")

