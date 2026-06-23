# Async Samples

This directory contains samples demonstrating asynchronous programming patterns with OpenZiti.

## Files

### `sample-async.py`
Raw socket-based async networking using `asyncio`.

**Features:**
- Non-blocking socket operations
- Async connection to Ziti services
- Concurrent requests using `asyncio.gather()`
- Direct HTTP protocol handling

**Usage:**
```bash
python sample-async.py <identity_file> <hostname:port>
```

---

### `sample-aiohttp.py`
Modern async HTTP client using `aiohttp` library.

**Features:**
- Simple HTTP GET/POST requests
- Multiple concurrent requests
- Error handling and timeouts
- Connection pooling via ClientSession

**Installation:**
```bash
pip install aiohttp
```

**Usage:**
```bash
python sample-aiohttp.py <identity_file> <url>
```

**Examples:**

With Ziti identity:
```bash
python sample-aiohttp.py ~/.ziti/identities/my-identity.json http://my.service.ziti/api
```

---

## Dependencies

- `openziti` - OpenZiti Python SDK
- `aiohttp` - For the HTTP client sample (install with `pip install aiohttp`)
- Python 3.7+ for asyncio support

---

For more information about OpenZiti, visit https://docs.openziti.io/

