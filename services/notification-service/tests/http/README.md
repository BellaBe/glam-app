# Notification Service HTTP Tests

## Quick Start

1. **Install VS Code REST Client Extension**
   - Extension ID: `humao.rest-client`
   - Or search "REST Client" in VS Code Extensions

2. **Configure Environment**
   - Copy `http-client.env.json.example` to `http-client.env.json`
   - Update tokens and URLs for your environment
   - **Never commit `http-client.env.json` with real tokens!**

3. **Run Tests**
   - Open `notifications.http`
   - Click "Send Request" above any request
   - Or use keyboard shortcut: `Ctrl+Alt+R` (Windows/Linux) or `Cmd+Alt+R` (Mac)

## Environment Setup

### Local Development
```bash
# Start the notification service locally
docker-compose up notification-service

# The service should be available at http://localhost:8000
```

### Switch Environments
1. Click environment name in VS Code status bar
2. Or use Command Palette: `Rest Client: Switch Environment`
3. Select: `local`, `dev`, `staging`, or `prod`

## Test Coverage

### Endpoints Tested
- `GET /notifications` - List notifications with pagination and filters
- `GET /notifications/stats` - Get notification statistics
- `GET /notifications/{id}` - Get specific notification

### Test Scenarios
✅ **Happy Paths**
- List notifications with valid auth
- Filter by status and merchant_id
- Pagination with different page sizes
- Get notification statistics
- Get specific notification by ID
- Complete workflow test (list → stats → get by ID)

❌ **Error Paths**
- 401 Unauthorized (missing auth token)
- 403 Forbidden (insufficient permissions)
- 404 Not Found (non-existent notification)
- 422 Validation Error (invalid UUID format)
- Invalid query parameters handling

🔧 **Edge Cases**
- Maximum limit boundary (100 items)
- Negative page numbers
- Invalid pagination parameters
- Request tracking headers preservation

## Variables & Chaining

The tests use variable extraction and chaining:
- `actual_notification_id` - Extracted from first notification in list
- `actual_merchant_id` - Used for filtering tests
- `workflow_notification_id` - Used in workflow tests
- `stats_sent_today`, `stats_failed_today` - Statistics validation

## Running in CI

### GitHub Actions Example
```yaml
name: API Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Generate env config
        run: |
          cat > tests/http/http-client.env.json <<EOF
          {
            "dev": {
              "notification_base_url": "${{ secrets.API_URL }}",
              "auth_token": "${{ secrets.AUTH_TOKEN }}",
              "auth_token_no_permissions": "${{ secrets.AUTH_TOKEN_NO_PERMS }}"
            }
          }
          EOF

      - name: Run tests
        run: |
          # Use a CLI tool like newman or rest-cli
          # Or create a script to execute .http files
```

### Using Newman (Postman CLI)
```bash
# Convert .http to Postman collection first
# Then run with Newman
newman run notification-tests.json -e environment.json
```

## Authentication

The API uses Bearer token authentication:
```
Authorization: Bearer {{auth_token}}
```

Required scopes:
- `notifications:read` - Read notifications and stats
- `notifications:write` - Write operations (not used in these tests)

## Response Format

All endpoints return standardized responses:
```json
{
  "success": true,
  "data": {...},
  "meta": {
    "page": 1,
    "limit": 10,
    "total": 100,
    "links": {...}
  },
  "request_id": "uuid",
  "correlation_id": "uuid"
}
```

## Notification Schema

```json
{
  "id": "uuid",
  "merchant_id": "string (uuid)",
  "platform_name": "string",
  "platform_shop_id": "string",
  "domain": "string",
  "recipient_email": "string",
  "template_type": "string",
  "template_variables": {},
  "status": "pending|sent|failed",
  "attempt_count": 0,
  "first_attempt_at": "datetime",
  "last_attempt_at": "datetime",
  "delivered_at": "datetime",
  "provider_message_id": "string",
  "provider_message": {},
  "idempotency_key": "string"
}
```

## Stats Schema

```json
{
  "sent_today": 0,
  "failed_today": 0,
  "pending_today": 0,
  "by_template": {
    "template_name": 0
  },
  "by_status": {
    "pending": 0,
    "sent": 0,
    "failed": 0
  }
}
```

## Troubleshooting

### Common Issues

1. **401 Unauthorized**
   - Check if auth token is valid
   - Ensure token has correct format
   - Verify token hasn't expired

2. **403 Forbidden**
   - Check token has required scopes
   - Verify `notifications:read` permission

3. **Variable not found**
   - Run tests sequentially from top
   - Ensure first list request succeeds
   - Check if data exists in response

4. **Connection refused**
   - Verify service is running
   - Check correct port and URL
   - Ensure no firewall blocking

### Debug Tips

- Use `client.log()` in test scripts to debug
- Check VS Code "REST Client" output panel
- Enable verbose logging in extension settings
- Test individual requests before workflows

## Contributing

When adding new tests:
1. Follow naming convention: `# @name descriptive_name`
2. Add assertions for status, content-type, and data
3. Extract variables for chaining when needed
4. Include both positive and negative test cases
5. Document expected behavior in comments
