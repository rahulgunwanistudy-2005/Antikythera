"""Edition-aware chaptering without changing any source offsets."""
import re

def culpeper_chapters(text):
    # This edition uses indented uppercase titles, and each botanical chapter
    # contains the recurring descriptive/government headings. Frontmatter and
    # later dispensatory sections fail that gate.
    heads=list(re.finditer(r'(?m)^ {4}([A-Z][A-Z ’‘\'(),.;&\-]{2,100})\s*$',text))
    chapters=[]
    for i,match in enumerate(heads):
        end=heads[i+1].start() if i+1<len(heads) else len(text)
        body=text[match.end():end]
        if not re.search(r'_Government and virtues?\._\]',body,re.I):continue
        if not re.search(r'_(Descript|Place|Time)\._\]',body,re.I):continue
        chapters.append({'title':match.group(1).strip(),'start':match.start(1),'title_end':match.end(1),'end':end,'text':text[match.start(1):end]})
    return chapters

def generic_chapters(text,heading_pattern=r'(?m)^#{1,4} (.+)$'):
    matches=list(re.finditer(heading_pattern,text))
    return [{'title':m.group(1),'start':m.start(),'title_end':m.end(),'end':matches[i+1].start() if i+1<len(matches) else len(text),'text':text[m.start():matches[i+1].start() if i+1<len(matches) else len(text)]} for i,m in enumerate(matches)]
