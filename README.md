# Run once per service repository (writes to services/<name>/.venv)
poetry config virtualenvs.in-project true --local
Poetry will now drop a .venv/ folder right next to the pyproject.toml inside every services/<name> directory.

Inside services/<SERVICE>/pyproject.toml add one line:

[tool.poetry.dependencies]
shared = { path = "../../shared", develop = true }
or run:
cd services/<SERVICE>
poetry add --path ../../shared --editable
Now poetry install will wire the shared code automatically and you can forget about manual PYTHONPATH hacks.
cd services/<SERVICE>          # e.g. catalog-service
poetry install                 # resolves + creates .venv
poetry shell                   # drops you inside that venv

cd /path/to/project          # repo root (same level as pyproject.toml)
pyenv local 3.12.3

pyenv shell 3.12.3           # for just this terminal session

poetry env use $(pyenv which python)   # inside the repo
Poetry will notice the interpreter path, create/repair the .venv, and remember.

Later you can swap versions the same way:
pyenv install 3.13.0rc1       # if you want a release-candidate
pyenv local 3.13.0rc1
poetry env use $(pyenv which python)