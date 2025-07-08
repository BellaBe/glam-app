# Init repo
alembic init migrations

# Generate migration skeleton (no autodetect)
alembic revision -m "manual change"

# Generate with diff
alembic revision --autogenerate -m "..."

# Apply to latest
alembic upgrade head

# Revert last migration
alembic downgrade -1

# See current revision
alembic current

# Mark DB as up-to-date without changes
alembic stamp head

# Apply / revert
alembic upgrade <rev|head>
alembic downgrade <rev|-1>

# Inspect
alembic heads         # show branch heads
alembic branches      # show diverging history
alembic merge <revA> <revB> -m "merge heads"
