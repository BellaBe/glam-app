#!/bin/bash
# Check health of services

ENV=$1

case $ENV in
    dev)
        COMPOSE_FILE="docker/docker-compose.dev.yml"
        ;;
    prod)
        COMPOSE_FILE="docker/docker-compose.prod.yml"
        ;;
    *)
        echo "Unknown environment: $ENV"
        exit 1
        ;;
esac

# Check if all services are healthy
UNHEALTHY=$(docker-compose -f $COMPOSE_FILE ps --format json | jq -r '.[] | select(.Health != "healthy" and .Health != null) | .Service')

if [ -n "$UNHEALTHY" ]; then
    echo "Unhealthy services: $UNHEALTHY"
    exit 1
fi

echo "All services are healthy"
exit 0
