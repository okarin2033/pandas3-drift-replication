import sys,re
from html.parser import HTMLParser
class P(HTMLParser):
    def __init__(s):
        super().__init__(); s.o=[]; s.skip=0; s.main=False
    def handle_starttag(s,t,a):
        a=dict(a)
        if t in('script','style','nav','footer'): s.skip+=1
        if t in('h1','h2','h3','h4'): s.o.append('\n\n'+'#'*int(t[1])+' ')
        if t in('p','li','pre','tr'): s.o.append('\n')
        if t=='a' and a.get('class') and 'headerlink' in a['class']: s.skip+=1; s.hl=1
        if a.get('id') and t in('section','span','h2','h3','h4') and t!='span': s.o.append(f'[#{a["id"]}] ')
    def handle_endtag(s,t):
        if t in('script','style','nav','footer'): s.skip-=1
        if t=='a' and getattr(s,'hl',0): s.skip-=1; s.hl=0
    def handle_data(s,d):
        if not s.skip: s.o.append(d)
p=P(); p.feed(open(sys.argv[1],encoding='utf8').read())
t=''.join(p.o); t=re.sub(r'\n\s*\n\s*\n+','\n\n',t); open(sys.argv[2],'w').write(t)
