import http.client

def ws_request(host, port, path, origin):
    conn = http.client.HTTPConnection(host, port, timeout=5)
    try:
        conn.connect()
        conn.request('GET', path, headers={
            'Host': '%s:%d' % (host, port),
            'Upgrade': 'websocket',
            'Connection': 'Upgrade',
            'Sec-WebSocket-Version': '13',
            'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
            'Origin': origin,
        })
        resp = conn.getresponse()
        print('Status:', resp.status, resp.reason)
        print('Headers:')
        for h in resp.getheaders():
            print(' ', h[0] + ':', h[1])
    except Exception as e:
        print('Error:', e)
    finally:
        conn.close()

print('--- Test 1: no origin ---')
ws_request('localhost', 8000, '/ws/camera', 'http://localhost:5173')

print()
print('--- Test 2: matching origin ---')
ws_request('localhost', 8000, '/ws/camera', 'http://localhost:5173')

print()
print('--- Test 3: different origin ---')
ws_request('localhost', 8000, '/ws/camera', 'http://evil.com')
