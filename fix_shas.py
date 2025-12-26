import os
import re

replacements = {
    r'actions/checkout@[0-9a-f]{40,}': 'actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683',
    r'actions/setup-python@[0-9a-f]{40,}': 'actions/setup-python@f67772396d47d85717b3a165f3d7907706243007',
    r'actions/github-script@[0-9a-f]{40,}': 'actions/github-script@60a0d83039c74a4aee543508d2ffcb1c3799cdea',
    r'actions/upload-artifact@[0-9a-f]{40,}': 'actions/upload-artifact@4ced58f8451302828c3cc5978436b107e382ff58',
    r'actions/download-artifact@[0-9a-f]{40,}': 'actions/download-artifact@cc203385981b70ca67e1cc392babf913a2f280ad',
    r'actions/add-to-project@[0-9a-f]{40,}': 'actions/add-to-project@244f685bbc3b7adfa8466e08b698b5577571133e',
    r'stefanzweifel/git-auto-commit-action@[0-9a-f]{40,}': 'stefanzweifel/git-auto-commit-action@e348103e9026cc0eee72306bc60bb5d27e1393a8',
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
dirs = ['.github/workflows', 'repository-files/always-sync/.github/workflows']
for d in dirs:
    if not os.path.isdir(d):
        continue
    for f in os.listdir(d):
        if f.endswith('.yml'):
            fix_file(os.path.join(d, f))
