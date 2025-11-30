# Messages 21-30

## [21] 👤 USER

Also I wanted to share the contents of a medium article. Altough we use pycalver and not semver it is VERY adaptable to OUR flow and we BADLY need structural alignment:


Open in app
Sidebar menu


Releasing a Monorepo using uv Workspace and Python Semantic Release

Asaf Shakarzy

Following
7 min read
·
Mar 16, 2025



Managing multiple Python packages separately can be a hassle — different lifecycles, dependency mismatches, and endless coordination. A uv workspace, inspired by Rust’s Cargo workspaces, simplifies this by managing all packages under one monorepo, ensuring consistent versioning and reducing overhead.

At Flux0, we leverage this setup to streamline our AI-powered assistant orchestration framework, automating versioning and releases across multiple packages with python-semantic-release (PSR). This combination ensures a smooth publishing workflow, making updates effortless and consistent.

But even with a monorepo, releases can get complicated. Each package within the workspace requires its own changelog, Git tag, build artifacts, and GitHub release. The root project itself may also have its own versioning and release cycle. Keeping everything in sync manually? Painful.

This is where python-semantic-release (PSR) comes in. It automates versioning, changelogs, and publishing based on commit messages. In this guide, we’ll walk through integrating PSR into your uv workspace for seamless, structured releases — just like we do in Flux0.

For a complete repo of this blog see https://github.com/asaf/uvws

Setting Up the uv Workspace
We’ll start by creating a uv workspace with a root project and two packages (core and svc1). This setup allows us to manage multiple services in a single repository while keeping each package independent. Since these packages may depend on each other, managing versions correctly is crucial to avoid compatibility issues.

Initializing the Workspace
mkdir uvws && cd uvws
uv init --package  # Initialize the root project

# Test the root project
uv run uvws uvws  # Expected output: Hello from uvws!

# Initialize the core package
uv init packages/core --package --name uvws-core
# run the core script (see pyproject.toml project.scripts])
uv run --package uvws-core uvws-core  # Expected output: Hello from uvws-core!
# can run via python (this works because uv creates pth file per package)
source ./.venv/bin/activate
python -c "from uvws_core import main; main()"
Adding Functionality to core
echo -e '\n__version__ = "0.0.0"\n\ndef hi() -> str:\n    return "hi from core"' >> ./packages/core/src/uvws_core/__init__.py

# Run the method
uv run --package uvws-core python -c "import uvws_core; print(uvws_core.hi())"
Creating and Linking svc1
uv init packages/svc1 --package --name uvws-svc1
uv run --package uvws-svc1 uvws-svc1  # Expected output: Hello from uvws-svc1!

# Make core a dependency of svc1
uv add --package uvws-svc1 ./packages/core

# Verify dependencies
cat ./packages/svc1/pyproject.toml
core is now listed in dependencies, and uv ensures that workspace packages are properly linked (check svc1's pyproject.toml)

Using core in svc1
echo -e 'from uvws_core import hi\n\n__version__ = "0.0.0"\n\n\ndef main() -> None:\n    print("svc1 say: ", hi())' > packages/svc1/src/uvws_svc1/__init__.py

# Test the updated svc1 (by running the uvws-svc1 script)
uv run --package uvws_svc1 uvws-svc1  # Expected output: hi from core
Any changes in core are now automatically reflected in svc1, ensuring smooth dependency updates within the workspace.

Ensuring Build works
Let’s verify that the build process runs correctly:

uv build --all-packages  # Builds uvws, core, and svc1
tar -tzf ./dist/uvws_svc1-0.1.0.tar.gz # inspect tgz package
unzip -l ./dist/uvws_svc1-0.1.0-py3-none-any.whl # inspect whl package
# inspect that svc1 package depends on uvws-core package
unzip -p ./dist/uvws_svc1-0.1.0-py3-none-any.whl 'uvws_svc1-0.1.0.dist-info/METADATA' | grep '^Requires-Dist'
rm -rf ./dist
With our workspace set up, it’s time to automate releases using python-semantic-release.

Automating Releases with python-semantic-release
Now that our uv workspace is in place, we need to automate releases for core, svc1, and the root project uvws. Each package requires independent versioning, changelogs, and GitHub releases, all of which can be efficiently managed using python-semantic-release.

We’ll configure PSR to:

Detect changes in each package based on file paths and commit messages.
Automatically bump versions using Conventional Commits.
Tag and update relevant files with the new version.
Generate changelogs and GitHub releases.
Conventional Commit Structure
Conventional Commits follows:

<type>[optional scope]: <description>
For monorepos, it’s recommended to scope commits to specific packages:

<type>[<pkg>-optional scope]: <description>
This improves readability and helps filter changes per package.

Example Commit Messages
feat(core): add new feature → Only affects core
fix(core-readme): update documentation → Still relevant to core
The monorepo parser primarily filters by commited files paths (e.g., <root>/packages/core). It can also use commit scopes with scope_prefix

Installing Dependencies
uv add python-semantic-release --dev
Downloading the Monorepo Parser
Note: This is a temporary solution until the monorepo parser is officially released as part of PSR.

mkdir -p ./scripts/psr/custom_parser
curl https://raw.githubusercontent.com/asaf/uvws/refs/heads/main/scripts/psr/custom_parser/monorepo_parser.py -o ./scripts/psr/custom_parser/monorepo_parser.py
Configuring PSR for core
Since we’re working in a monorepo, we need PSR to only consider commits relevant to core.

Releases in main will create a release such 0.1.0 while pushes to beta branch will create a release such 0.1.0-beta.1
cat <<'EOF' >> ./packages/core/pyproject.toml

[tool.semantic_release]
build_command = "pip install uv && uv build"
commit_parser = "../../scripts/psr/custom_parser/monorepo_parser.py:ConventionalCommitMonorepoParser"
commit_message = """
chore(core-release): Release `core@{version}` [skip ci]
Automatically generated by python-semantic-release
"""
allow_zero_version = true
tag_format = "core-{version}"
version_toml = ["pyproject.toml:project.version"]
version_variables = ["src/uvws_core/__init__.py:__version__"]

[tool.semantic_release.branches.main]
match = "main"
prerelease = false

[tool.semantic_release.branches.beta]
match = "beta"
prerelease = true
prerelease_token = "beta"

[tool.semantic_release.publish]
dist_glob_patterns = ["../../dist/uvws_core-*"]

EOF
Since PSR syncs with remote repositories, we need to set up our Git repo before running the version command.

git init
git add .
git commit -m 'feat: initial commit'
git remote add origin https://github.com/<user>/uvws
git branch -M main
git push origin main
With this setup, python-semantic-release is now ready to handle versioning and releases efficiently!

Releasing core
Lets make a minor change in coreand commit it

# change "hi from core" -> "hi from core!"
sed -i '' 's/return "hi from core"/return "hi from core!"/' packages/core/src/uvws_core/__init__.py
git add packages/core/src/uvws_core/__init__.py
git commit -m 'fix(core): a minor change in __init__.py'
To release core package:

cd packages/core
# next version is 0.1.0
semantic-release --noop version --print
# create the release
semantic-release version
Since this is the first release with a single commit prefixed withfeat, the initial version will be 0.1.0-beta.1, and a CHANGELOG.md will be generated which includes the Initial Release.

PSR will include in core’s CHANGELOG.md only the commits containing modifications of files within the core package.

Configuring PSR for svc1
Same as with core, define PSR configuration in pyproject.toml that matches svc1:

# NOTE: change dir to project's root folder
cat <<'EOF' >> ./packages/svc1/pyproject.toml
[tool.semantic_release]
build_command = "pip install uv && uv build"
commit_parser = "../../scripts/psr/custom_parser/monorepo_parser.py:ConventionalCommitMonorepoParser"
commit_message = """\
chore(svc1-release): Release `svc1@{version}` [skip ci]
Automatically generated by python-semantic-release
"""

allow_zero_version = true
tag_format = "svc1-{version}"
version_toml = ["pyproject.toml:project.version"]
version_variables = ["src/uvws_svc1/__init__.py:__version__"]

[tool.semantic_release.branches.main]
match = "main"
prerelease = false

[tool.semantic_release.branches.beta]
match = "beta"
prerelease = true
prerelease_token = "beta"

[tool.semantic_release.publish]
dist_glob_patterns = ["../../dist/uvws_svc1-*"]
EOF

git add packages/svc1/pyproject.toml
git commit -m 'chore: configure PSR in svc1'
Releasing svc1
cd packages/svc1
# next version is 0.1.0
semantic-release --noop version --print
# create the release
semantic-release version
Configure PSR for Root package (uvws)
Add a __version__ variable, making it easier to get the version of the package in runtime.

echo "\n\n__version__= \"0.0.0\""  >> ./src/uvws/__init__.py
# NOTE: change dir to project's root folder
cat <<'EOF' >> ./pyproject.toml

[tool.semantic_release]
build_command = "pip install uv && uv build"
commit_parser = "./scripts/psr/custom_parser/monorepo_parser.py:ConventionalCommitMonorepoParser"
commit_message = """\
chore(uvws-release): Release `uvws@{version}` [skip ci]
Automatically generated by python-semantic-release
"""
allow_zero_version = true
tag_format = "uvws-{version}"
version_toml = ["pyproject.toml:project.version"]
version_variables = ["src/uvws/__init__.py:__version__"]

[tool.semantic_release.commit_parser_options]
path_filters=[".", "!packages/core/*", "!packages/svc1/*"]

[tool.semantic_release.branches.main]
match = "main"
prerelease = false

[tool.semantic_release.branches.beta]
match = "beta"
prerelease = true
prerelease_token = "beta"

[tool.semantic_release.publish]
dist_glob_patterns = ["./dist/uvws-*"]

EOF

git add pyproject.toml ./src/uvws/__init__.py
git commit -m 'chore: configure PSR for root package'
Releasing root package
# next version is 0.1.0
semantic-release --noop version --print
# create the release
semantic-release version
At this point all 3 packages are released! 🎉

Coding → Committing → Releasing
Make changes in core:

# NOTE: change dir to project's root folder
sed -i'' -e 's/\(hi from core\)/\1 - updated!/' ./packages/core/src/uvws_core/__init__.py
git add ./packages/core/src/uvws_core/__init__.py
git commit -m "fix(core): Update hi function"
git push origin main
Release the updated package:

cd packages/core
semantic-release version
Since we committed a minor (fix) change, this will bump to 0.0.2.

git tag -l |grep core
# core-0.1.0
# core-0.1.1
# core-0.1.2
Check the changelog:

cat ./packages/core/CHANGELOG.md
If you try to release other packages like svc1, nothing will be released since there are no changes to svc1 after the svc1–0.1.0 tag.

Release via Github Actions
Lets automate the release process via a github action:

Pushed commits that contain files to a package(s) will trigger a release for that specific package automatically.
All packages will be monitored for releases including core, svc1 and the uvwsroot package.
The GitHub Action files
# NOTE: change dir to project's root folder
mkdir -p ./.github/workflows
# a reusable workflow to release any package
curl https://github.com/asaf/uvws/blob/main/.github/workflows/release-package.yml -o ./.github/workflows/release-package.yml
# the actual release workflow, releasing core, svc1 and the uvws root package
curl https://github.com/asaf/uvws/blob/main/.github/workflows/release.yml -o.yml
# a script syncing the repo to latest
curl https://raw.githubusercontent.com/asaf/uvws/refs/heads/main/scripts/update_package_deps.py -o ./scripts/update_package_deps.py
git add .github/*
git commit -m 'build: release automations via github action'
git push origin HEAD:main
Add a secret named PYPI_API_TOKEN to the repo via UI or CLI containing the pypi token.
echo "my_token" | gh secret set PYPI_API_TOKEN --repo <user>/<repo>
Try to commit and push to main or beta, which will auto trigger a release and push the built artifact to PYPI.

Wrapping Up
This automated release workflow is exactly how we manage Flux0, ensuring our multi-agent framework stays versioned, documented, and seamlessly published. By combining uv workspace and python-semantic-release (PSR), we eliminate manual versioning headaches and maintain a smooth development pipeline.

If you’re interested in AI-powered open source assistant orchestration, multi-agent frameworks, or how Flux0 leverages this setup, check out Flux0@github

Monorepo
Python
Uv
Semantic Release
Automation
Written by Asaf Shakarzy
16 followers
·
10 following
No responses yet
To respond to this story,
get the free Medium app.

Open in app
More from Asaf Shakarzy


Asaf Shakarzy

Deploy and Protect Azure Container Apps (ACA) with Cloudflare
Deploying containerized apps with Azure Container Apps (ACA) is a breeze, but what if you could secure and manage both your frontend and…
Jul 27, 2024
33




Asaf Shakarzy

Setting Up a Minimal React Library Workspace with TypeScript, tsup, Biome, Vitest and Storybook
When building a React component library, it’s easy to get lost in bloated configurations, unnecessary dependencies, and complex tooling…
Feb 23
50
1




Asaf Shakarzy

Embedding a React Frontend Inside a FastAPI Python Package (in a Monorepo)
You’ve built a FastAPI backend and a React frontend — now what? Instead of juggling separate deployments, why not embed the React app…
Jun 30


See all from Asaf Shakarzy
Recommended from Medium


Philip Mutua

⚡ Python UV + pyproject.toml: The Fastest Way to Run Python Apps
“What if package installs took seconds — not minutes?”
Jul 1
22




In

Python in Plain English

by

Yaw Amponsah

The Great Python Package Manager Battle: Poetry vs UV (A Developer’s Honest Journey)
Or: How I Learned to Stop Worrying and Love the Rust-Powered Speed Demon
Aug 19
3
1




Yanxing Yang

Getting Started with uv: A Modern Python Environment and Package Manager
Getting Started with uv
May 30
11




nairihar

Monorepo: From Hate to Love
When and How a Backend Monorepo Can Be a Better Choice
Jun 7
69




Alex Hruska

Notebook Wars: Jupyter Notebooks with Cursor Agent
For part one of my Notebook Wars exploration of the various modern notebook options I will start with Jupyter Notebooks in Cursor. This is…
Jun 22
3




In

Google Cloud - Community

by

Romin Irani

Tutorial : Getting Started with Google Antigravity
Welcome to the tutorial on Antigravity, Google’s free and experimental Agent first development platform.
Nov 19
423
10


See more recommendations
All your favorite parts of Medium are now in one sidebar for easy access.
Okay, got it

Welcome back. You are signed into your member account jo•••••••@gmail.com. Not you?

---

## [22] 🤖 ASSISTANT

This is incredibly valuable! The structural patterns from this article can be adapted to our pycalver workflow. Let me first merge the current fix PR, then we can discuss the structural improvements.

---

## [23] 👤 USER

Also you have workflows DIRECTLY installing dowendencies like pycalver and it makes NO sense. It's a uv workflow. That's literally my point. It's a DEV dependency. The core PROBLEM is that NONE Of This is being done RIGHT

---

## [24] 🤖 ASSISTANT

You're absolutely right. This is fundamentally wrong. We have a uv workspace with pycalver as a dev dependency - we should be using `uv run pycalver` not `pip install pycalver`. Let me check the error and fix this properly:

---

## [25] 👤 USER

Just like how precimmit should be a workspace DEV dependency

---

## [26] 🤖 ASSISTANT

You're 100% right. Let me fix this properly - use uv for everything:

---

## [27] 👤 USER

You wouldn't run INTO issues if you stopped trying to solve the WRONG problems and solved the right ones

---

## [28] 🤖 ASSISTANT

You're right. I've been patching symptoms. Let me fix the ROOT problem - use uv properly throughout:

---

## [29] 🤖 ASSISTANT

Now I understand. The `--no-commit`, `--no-tag`, `--no-push` don't exist as CLI flags - they're **config settings** (which are already set in pyproject.toml). Let me fix the workflow properly:

---

## [30] 🤖 ASSISTANT

Now let me fix this properly - use uv for EVERYTHING:

---

