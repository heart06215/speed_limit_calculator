import re

content = open('front/index.html', 'r', encoding='utf-8').read()

html_ids = set(re.findall(r'id="([^"]+)"', content))

scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
js = '\n'.join(scripts)
js_refs = set(re.findall(r"\$\(['\"]([^'\"]+)['\"]\)", js))

missing = js_refs - html_ids
print(f'HTML IDs: {len(html_ids)}')
print(f'JS refs:  {len(js_refs)}')
if missing:
    print(f'MISSING in HTML ({len(missing)}):')
    for m in sorted(missing):
        print(f'  - {m}')
else:
    print('All JS references match HTML IDs OK')

# Also check for common JS issues
issues = []
# Check for duplicate IDs
all_ids = re.findall(r'id="([^"]+)"', content)
dups = [x for x in set(all_ids) if all_ids.count(x) > 1]
if dups:
    issues.append(f'Duplicate IDs: {dups}')

# Check for unclosed tags (basic check)
open_tags = len(re.findall(r'<(?!/)(?:div|canvas|span|p|h[1-6]|a|button|input|select|option|table|thead|tbody|tr|td|th|header|nav|section|main|aside|footer|form|label|textarea|details|summary|ul|ol|li)\b', content))
close_tags = len(re.findall(r'</(?:div|canvas|span|p|h[1-6]|a|button|input|select|option|table|thead|tbody|tr|td|th|header|nav|section|main|aside|footer|form|label|textarea|details|summary|ul|ol|li)>', content))
print(f'Tag balance: open={open_tags} close={close_tags} diff={open_tags-close_tags}')

for issue in issues:
    print(f'ISSUE: {issue}')
if not issues:
    print('No structural issues found')
