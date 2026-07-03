with open('src/ocr_correction/adapters.py', 'r') as f:
    content = f.read()

import re
content = re.sub(r'\n\n\n+', '\n\n', content)

with open('src/ocr_correction/adapters.py', 'w') as f:
    f.write(content)
