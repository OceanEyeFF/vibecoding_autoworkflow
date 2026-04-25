#!/usr/bin/env python3
from pathlib import Path

root = Path('/mnt/e/repos/WSL/personal/vibecoding_autoworkflow/product/harness/skills')

repls = [
    ('gpt-5.4-xhigh', '通用高能力模型'),
    ('gpt-5.4-xhigh 子代理', '通用高能力子代理'),
    ('gpt-5.4-xhigh `子代理`', '通用高能力 `子代理`'),
    ('gpt-5.4-xhigh `SubAgent`', '通用高能力 `SubAgent`'),
    ('gpt-5.4-xhigh SubAgent', '通用高能力 SubAgent'),
]

count = 0
for p in root.rglob('SKILL.md'):
    text = p.read_text(encoding='utf-8')
    new = text
    for a, b in repls:
        new = new.replace(a, b)
    if new != text:
        p.write_text(new, encoding='utf-8')
        print(f"Updated: {p}")
        count += 1

print(f"Total updated: {count}")
