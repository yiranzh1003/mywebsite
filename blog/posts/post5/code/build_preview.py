"""Build a self-contained browser preview after analyze.py; standard library only."""
from pathlib import Path
import re,html,base64
root=Path(__file__).resolve().parents[1]
source=(root/'article.md').read_text()
def inline(s):
 s=html.escape(s)
 s=re.sub(r'\[([^]]+)\]\((https?://[^)]+)\)',r'<a href="\2">\1</a>',s)
 s=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',s)
 return s
blocks=[]
for block in source.split('\n\n'):
 block=block.strip()
 if not block:continue
 if block.startswith('# '):blocks.append('<h1>'+inline(block[2:])+'</h1>');continue
 match=re.fullmatch(r'!\[([^]]+)\]\(([^)]+)\)',block)
 if match:
  alt,path=match.groups();data=base64.b64encode((root/path).read_bytes()).decode()
  blocks.append(f'<figure><img alt="{html.escape(alt)}" src="data:image/png;base64,{data}"><figcaption>{html.escape(alt)}</figcaption></figure>');continue
 if block.startswith('*') and block.endswith('*'):blocks.append('<p class="source">'+inline(block[1:-1])+'</p>')
 else:blocks.append('<p>'+inline(block)+'</p>')
style='body{margin:0;background:#faf9f6;color:#20252b;font-family:Georgia,serif}article{max-width:850px;margin:50px auto;padding:35px;background:white}h1{font-size:42px;line-height:1.15}p{font-size:19px;line-height:1.75}a{color:#24546d}figure{margin:32px -15px}img{width:100%;height:auto}figcaption,.source{font:14px/1.55 Arial,sans-serif;color:#555}header{font:13px Arial,sans-serif;letter-spacing:1px;color:#61717c} @media(max-width:650px){article{margin:0;padding:24px}h1{font-size:32px}p{font-size:17px}figure{margin:25px 0}}'
(root/'preview.html').write_text('<!DOCTYPE html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Philadelphia Rent and Affordability</title><style>'+style+'</style><article><header>YIRAN ZHANG · OCTOBER 19, 2026</header>'+''.join(blocks)+'</article></html>')
print('preview.html created')
