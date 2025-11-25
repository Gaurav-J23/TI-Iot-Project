# Troubleshooting Pi Host App Connection

## Issue: "This site can't be reached - 192.168.1.80 took too long to respond"

### Step 1: Verify Pi is on Network
```bash
# From your PC, ping the Pi
ping 192.168.1.80

# Should see replies if Pi is reachable
```

### Step 2: Check if Host App is Running on Pi
SSH into the Pi and check:
```bash
ssh ubuntu@192.168.1.80

# Check if Host App process is running
ps aux | grep python
# or
ps aux | grep uvicorn

# Check if port 8010 is listening
sudo netstat -tlnp | grep 8010
# or
sudo ss -tlnp | grep 8010
```

### Step 3: Verify Host App is Accessible Locally on Pi
On the Pi itself, test:
```bash
curl http://localhost:8010/health
# Should return: {"status":"healthy"}
```

### Step 4: Check Firewall on Pi
```bash
# Check firewall status
sudo ufw status

# If firewall is active, allow port 8010
sudo ufw allow 8010/tcp
sudo ufw reload
```

### Step 5: Verify Host App Configuration
Make sure the Host App is:
- Running on `0.0.0.0` (not `127.0.0.1`) to accept external connections
- Bound to port `8010`
- Not blocked by Pi's firewall

### Step 6: Check Network Connectivity
```bash
# From your PC, test if you can reach Pi
ping 192.168.1.80

# Test if port is accessible
telnet 192.168.1.80 8010
# (Press Ctrl+] then type 'quit' to exit)
```

### Common Issues:

1. **Host App not running**
   - Solution: Start the Host App on Pi
   - Command: `python main.py` or `uvicorn main:app --host 0.0.0.0 --port 8010`

2. **Firewall blocking port**
   - Solution: Allow port 8010 in Pi firewall
   - Command: `sudo ufw allow 8010/tcp`

3. **Host App bound to localhost only**
   - Solution: Make sure Host App uses `--host 0.0.0.0` not `--host 127.0.0.1`

4. **Wrong IP address**
   - Solution: Verify Pi IP with `ip addr` or `hostname -I` on Pi

5. **Different network**
   - Solution: Ensure PC and Pi are on same network (192.168.1.x)

### Quick Test Commands:

**On Pi:**
```bash
# Start Host App (if not running)
cd /path/to/host/app
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 8010

# Test locally
curl http://localhost:8010/health
```

**On PC:**
```bash
# Test connection
curl http://192.168.1.80:8010/health

# Or use browser
http://192.168.1.80:8010/health
```

