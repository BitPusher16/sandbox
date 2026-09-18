# uv quick ref:
uv python list
uv python install 3.12
uv python pin 3.13	# create a .python-version file for current project dir.
uv venv			# create a standard .venv using pinned or newest python version.
uv venv --python 3.11	# create venv bound to python version.
uv run python script.py	# runs script in venv without needing activation script.
uv init my-project	# initialize fresh project with pyproject.toml file.
uv add requests		# install package, add to pyproject.toml, write uv.lock.
uv remove requests
uv sync

# you can still activate if you wish:
source .venv/bin/activate

# modern new project workflow:
uv init my-project --python 3.12 # or uv init . --python 3.12
cd my-project
uv venv

# run with (note uv init replaces underscores with hyphens):
uv run grok-fluid-sim-tutorial

