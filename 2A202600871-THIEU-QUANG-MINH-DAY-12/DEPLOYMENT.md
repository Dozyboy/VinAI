# Deployment Information

## Public URL
https://balanced-perception-production-07ae.up.railway.app

## Platform
Railway

## Test Commands

### Health Check
```bash
curl https://balanced-perception-production-07ae.up.railway.app/health
# Expected: {"status": "ok"}
```

### API Test (with authentication)
```bash
curl -X POST https://balanced-perception-production-07ae.up.railway.app/ask \
  -H "X-API-Key: my-secret-key-123" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "question": "Hello"}'
```

## Environment Variables Set
- PORT
- REDIS_URL
- AGENT_API_KEY
- LOG_LEVEL

## Screenshots
- [Deployment dashboard](screenshots/dashboard.png)
- [Service running](screenshots/running.png)
- [Test results](screenshots/test.png)
