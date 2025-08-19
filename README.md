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


# Server info
curl http://localhost:8222/varz

# JetStream info
curl http://localhost:8222/jsz

# Connections info
curl http://localhost:8222/connz

# Subscriptions info
curl http://localhost:8222/subsz

# Routes info
curl http://localhost:8222/routez

# Install NATS CLI if you haven't
curl -L https://github.com/nats-io/natscli/releases/latest/download/nats-linux-amd64.zip -o nats.zip
unzip nats.zip && sudo mv nats /usr/local/bin/

# Monitor events in real-time
nats sub ">" # Subscribe to everything
nats sub "evt.notification.*" # Just notification events
nats sub "cmd.notification.*" # Just notification commands

# Check stream status
nats stream ls
nats stream info NOTIFICATION
nats consumer info NOTIFICATION notification-send-email

# Monitor JetStream
nats server report jetstream


poetry env list
$ pyenv local 3.11.9
poetry env use python3.11
poetry install
poetry shell
python --version


# Setup a service (first time only)
make local-setup SERVICE=notification-service
make db-push SERVICE=notification-service

# Run a single service
make local-run SERVICE=notification-service

# Run all services in parallel
make local-run-all

# Check status
make local-status

# View logs (infrastructure)
make local-logs

# Database operations
make db-studio SERVICE=notification-service  # Visual DB editor
make db-url SERVICE=notification-service     # Get connection string
