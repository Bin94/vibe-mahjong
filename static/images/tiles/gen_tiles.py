import os

out_dir = r'D:\KimiGC\vibe-mahjong\static\images\tiles'

def manzu(n):
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 80" width="60" height="80">
  <rect x="1" y="1" width="58" height="78" rx="6" fill="#f8f6f0" stroke="#2a2a2a" stroke-width="1.5"/>
  <text x="30" y="32" text-anchor="middle" font-size="22" font-weight="bold" fill="#c41e3a" font-family="serif">{n}</text>
  <text x="30" y="62" text-anchor="middle" font-size="26" fill="#2e7d32" font-family="serif">萬</text>
</svg>'''

def pinzu_dots(n):
    dots = {
        1: [(30,40)],
        2: [(30,24),(30,56)],
        3: [(30,20),(30,40),(30,60)],
        4: [(20,24),(40,24),(20,56),(40,56)],
        5: [(20,20),(40,20),(30,40),(20,60),(40,60)],
        6: [(20,22),(40,22),(20,40),(40,40),(20,58),(40,58)],
        7: [(30,14),(20,30),(40,30),(20,46),(40,46),(20,62),(40,62)],
        8: [(20,18),(40,18),(20,34),(40,34),(20,50),(40,50),(20,66),(40,66)],
        9: [(20,16),(40,16),(20,32),(40,32),(30,40),(20,56),(40,56),(20,68),(40,68)],
    }
    r = 7 if n <= 3 else 6
    circles = '\n'.join([f'  <circle cx="{x}" cy="{y}" r="{r}" fill="#c41e3a" stroke="#8b0000" stroke-width="0.5"/>' for x,y in dots[n]])
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 80" width="60" height="80">
  <rect x="1" y="1" width="58" height="78" rx="6" fill="#f8f6f0" stroke="#2a2a2a" stroke-width="1.5"/>
{circles}
</svg>'''

def souzu_bars(n):
    bars_data = {
        1: [(30,40,28)],
        2: [(22,40,10),(38,40,10)],
        3: [(18,40,8),(30,40,8),(42,40,8)],
        4: [(18,30,8),(18,50,8),(42,30,8),(42,50,8)],
        5: [(15,28,7),(30,28,7),(45,28,7),(15,52,7),(45,52,7)],
        6: [(16,26,7),(30,26,7),(44,26,7),(16,54,7),(30,54,7),(44,54,7)],
        7: [(30,18,6),(16,34,7),(44,34,7),(16,50,7),(44,50,7),(16,66,7),(44,66,7)],
        8: [(15,20,6),(30,20,6),(45,20,6),(15,40,6),(45,40,6),(15,60,6),(30,60,6),(45,60,6)],
        9: [(15,18,6),(30,18,6),(45,18,6),(15,36,6),(30,36,6),(45,36,6),(15,58,6),(30,58,6),(45,58,6)],
    }
    bars = []
    for x,y,h in bars_data[n]:
        bars.append(f'  <rect x="{x-3}" y="{y-h//2}" width="6" height="{h}" rx="2" fill="#2e7d32" stroke="#1b5e20" stroke-width="0.5"/>')
    bars_svg = '\n'.join(bars)
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 80" width="60" height="80">
  <rect x="1" y="1" width="58" height="78" rx="6" fill="#f8f6f0" stroke="#2a2a2a" stroke-width="1.5"/>
{bars_svg}
</svg>'''

def jihai(char, color, name):
    if name == 'white':
        return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 80" width="60" height="80">
  <rect x="1" y="1" width="58" height="78" rx="6" fill="#f8f6f0" stroke="#2a2a2a" stroke-width="1.5"/>
  <rect x="18" y="28" width="24" height="24" rx="3" fill="none" stroke="#2a2a2a" stroke-width="2.5"/>
</svg>'''
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 80" width="60" height="80">
  <rect x="1" y="1" width="58" height="78" rx="6" fill="#f8f6f0" stroke="#2a2a2a" stroke-width="1.5"/>
  <text x="30" y="52" text-anchor="middle" font-size="34" font-weight="bold" fill="{color}" font-family="serif">{char}</text>
</svg>'''

# 万子
for i in range(1,10):
    with open(os.path.join(out_dir, f'm{i}.svg'), 'w', encoding='utf-8') as f:
        f.write(manzu(i))

# 筒子
for i in range(1,10):
    with open(os.path.join(out_dir, f'p{i}.svg'), 'w', encoding='utf-8') as f:
        f.write(pinzu_dots(i))

# 条子
for i in range(1,10):
    with open(os.path.join(out_dir, f's{i}.svg'), 'w', encoding='utf-8') as f:
        f.write(souzu_bars(i))

# 字牌
jihai_list = [
    ('east', '東', '#2a2a2a'),
    ('south', '南', '#2a2a2a'),
    ('west', '西', '#2a2a2a'),
    ('north', '北', '#2a2a2a'),
    ('white', '', '#2a2a2a'),
    ('green', '發', '#2e7d32'),
    ('red', '中', '#c41e3a'),
]

for name, char, color in jihai_list:
    svg = jihai(char, color, name)
    with open(os.path.join(out_dir, f'{name}.svg'), 'w', encoding='utf-8') as f:
        f.write(svg)

print('Done! Generated', len(os.listdir(out_dir)), 'tiles')
