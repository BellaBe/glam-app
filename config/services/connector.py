# config/services/platform-connector.yml
service:
  name: "platform-connector"

# Connector-specific settings
connector:
  shopify_api_version: "2024-01"
  shopify_bulk_poll_interval_sec: 10
  shopify_bulk_timeout_sec: 600
  shopify_rate_limit_per_sec: 4
  rate_limit_window_sec: 60
  batch_size: 100
  max_retries: 3

# No API port since this is a background service
api:
  port: 8011
  external_port: 8011

database:
  enabled: true

features:
  cache_enabled: true
  max_retries: 3