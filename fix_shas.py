import os
import re

replacements = {
    r'actions/checkout@[0-9a-f]{40,}': 'actions/checkout@8e8c483db84b4bee98b60c0593521ed34d9990e8',
    r'actions/setup-python@[0-9a-f]{40,}': 'actions/setup-python@83679a892e2d95755f2dac6acb0bfd1e9ac5d548',
    r'actions/github-script@[0-9a-f]{40,}': 'actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd',
    r'actions/upload-artifact@[0-9a-f]{40,}': 'actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f',
    r'actions/download-artifact@[0-9a-f]{40,}': 'actions/download-artifact@37930b1c2abaa49bbe596cd826c3c89aef350131',
    r'actions/add-to-project@[0-9a-f]{40,}': 'actions/add-to-project@244f685bbc3b7adfa8466e08b698b5577571133e',
    r'stefanzweifel/git-auto-commit-action@[0-9a-f]{40,}': 'stefanzweifel/git-auto-commit-action@04702edda442b2e678b25b537cec683a1493fcb9',
    r'pozil/auto-assign-issue@[0-9a-f]{40,}': 'pozil/auto-assign-issue@39c06395cbac76e79afc4ad4e5c5c6db6ecfdd2e'
}

def fix_file(path):
    with open(path, 'r') as f:
        content = f.read()
    
    new_content = content
    for pattern, replacement in replacements.items():
        new_content = re.sub(pattern, replacement, new_content)
    
    if new_content != content:
        with open(path, 'w') as f:
            f.write(new_content)
        print(f"Fixed {path}")

# Workflows to check
dirs = ['.github/workflows', 'sync-files/always-sync/global/.github/workflows']
for d in dirs:
    if not os.path.isdir(d):
        continue
    for f in os.listdir(d):
        if f.endswith('.yml'):
            fix_file(os.path.join(d, f))
