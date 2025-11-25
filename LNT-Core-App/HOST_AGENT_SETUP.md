# Host Agent Configuration Setup

## Environment Variable Configuration

The Core App now uses environment variables to connect to the Host Agent.

### Step 1: Create `.env` file

Create a `.env` file in the `LNT-Core-App` directory with:

```env
HOST_AGENT_URL=http://192.168.1.80:8010/
```

### Step 2: Verify Configuration

The Core App will automatically load the `.env` file on startup.

### Step 3: Test Connection

Test the Core → Host connection:

```bash
# Via API
curl http://localhost:8000/device/test-connection

# Or via browser
http://localhost:8000/device/test-connection
```

Expected response if connection works:
```json
{
  "status": "success",
  "message": "Core → Host connection working",
  "host_url": "http://192.168.1.80:8010",
  "health_response": {"status": "healthy"}
}
```

## Host Agent Endpoints

The Core App expects these endpoints on the Host Agent:

- `GET ${HOST_AGENT_URL}/health` → `{"status": "healthy"}`
- `GET ${HOST_AGENT_URL}/duts` → `{"count": int, "types": list}`

## Fallback Behavior

If `HOST_AGENT_URL` is not set in `.env`, the Core App will:
- Default to `http://localhost:8001/`
- Use IP addresses from inventory.yml if available

## Network Configuration

**Pi Host Info:**
- IP: 192.168.1.80
- Hostname: ubuntu
- Port: 8010
- Interfaces: eth0 + wlan0 (wifi active)

Make sure the Core App can reach the Pi at `192.168.1.80:8010`.

