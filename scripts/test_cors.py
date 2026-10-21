import http.client
conn = http.client.HTTPConnection('localhost', 8000, timeout=5)
try:
    conn.connect()
    conn.request('GET', '/api/health', headers={
        'Host': 'localhost:8000',
        'Origin': 'http://localhost:5173',
    })
    resp = conn.getresponse()
    print('Status:', resp.status)
    cors = [h for h in resp.getheaders() if 'access-control' in h[0].lower()]
    print('CORS Headers:', cors)
except Exception as e:
    print('Error:', e)
finally:
    conn.close()
