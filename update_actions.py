import os
import re

mapping = {
    r'actions/checkout(@[0-9a-f]+|@v[0-9]+)?': 'actions/checkout@8e8c483db84b4bee98b60c0593521ed34d9990e8',
    r'actions/setup-python(@[0-9a-f]+|@v[0-9]+)?': 'actions/setup-python@83679a892e2d95755f2dac6acb0bfd1e9ac5d548',
    r'actions/setup-node(@[0-9a-f]+|@v[0-9]+)?': 'actions/setup-node@395ad3262231945c25e8478fd5baf05154b1d79f',
    r'actions/upload-artifact(@[0-9a-f]+|@v[0-9]+)?': 'actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f',
    r'actions/download-artifact(@[0-9a-f]+|@v[0-9]+)?': 'actions/download-artifact@37930b1c2abaa49bbe596cd826c3c89aef350131',
    r'actions/github-script(@[0-9a-f]+|@v[0-9]+)?': 'actions/github-script@ed597411d8f924073f98dfc5c65a23a2325f34cd',
    r'stefanzweifel/git-auto-commit-action(@[0-9a-f]+|@v[0-9]+)?': 'stefanzweifel/git-auto-commit-action@04702edda442b2e678b25b537cec683a1493fcb9',
    r'pozil/auto-assign-issue(@[0-9a-f]+|@v[0-9]+)?': 'pozil/auto-assign-issue@39c06395cbac76e79afc4ad4e5c5c6db6ecfdd2e',
    r'actions/add-to-project(@[0-9a-f]+|@v[0-9]+)?': 'actions/add-to-project@244f685bbc3b7adfa8466e08b698b5577571133e',
    r'peter-evans/create-pull-request(@[0-9a-f]+|@v[0-9]+)?': 'peter-evans/create-pull-request@5e914681df9dc83aa4e4905692ca88beb2f9e91f'
}

def update_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    new_content = content
    for pattern, replacement in mapping.items():
        # Match uses: pattern
        full_pattern = r'uses:\s+' + pattern
        new_content = re.sub(full_pattern, 'uses: ' + replacement, new_content)
    
    if new_content != content:
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

# Find all yml files
for root, dirs, files in os.walk('.'):
    if '.git' in dirs:
        dirs.remove('.git')
    for file in files:
        if file.endswith('.yml'):
            update_file(os.path.join(root, file))
