# alembic/README.md

# Alembic Migration Commands

## Create a new migration
```bash
alembic revision --autogenerate -m "description"
```

## Apply migrations
```bash
alembic upgrade head
```

## Rollback migration
```bash
alembic downgrade -1
```

## Show current revision
```bash
alembic current
```

## Show migration history
```bash
alembic history
```