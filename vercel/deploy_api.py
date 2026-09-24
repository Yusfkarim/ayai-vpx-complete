"""Deploy vercel/ to Vercel via API (no CLI, no git). Reads ~/.vtok. Usage: python3 deploy_api.py"""
import hashlib, json, os, sys, time
import requests
VTOK = open(os.path.expanduser('~/.vtok')).read().strip()
PID = 'prj_yuY4OK8NP7xhS0OPz8mmCTNO5fXH'
ROOT = os.path.dirname(os.path.abspath(__file__))
FILES = ['vercel.json', 'requirements.txt', 'api/chat.py', 'api/cron.py', 'api/models.py',
         'lib/_ported_raw.py', 'lib/kv.py', 'lib/providers.py', 'lib/shim.py']
H = {'Authorization': 'Bearer ' + VTOK}
entries = []
for f in FILES:
    b = open(os.path.join(ROOT, f), 'rb').read()
    s = hashlib.sha1(b).hexdigest()
    r = requests.post('https://api.vercel.com/v2/files', headers={**H, 'Content-Type': 'application/octet-stream',
                      'x-vercel-digest': s}, data=b, timeout=90)
    print(f, r.status_code, str(r.text)[:120], flush=True)
    if r.status_code not in (200, 201):
        sys.exit('UPLOAD-FAIL ' + f)
    entries.append({'file': f, 'sha': s, 'size': len(b)})
dep = requests.post('https://api.vercel.com/v13/deployments', headers={**H, 'Content-Type': 'application/json'},
                    json={'name': 'ayai-vpx', 'project': PID, 'target': 'production', 'files': entries,
                          'projectSettings': {'framework': None}}, timeout=90)
print('CREATE:', dep.status_code, flush=True)
d = dep.json()
if dep.status_code not in (200, 201):
    print(str(d)[:600])
    sys.exit('CREATE-FAIL')
did, url = d.get('id'), d.get('url')
print('ID:', did, 'URL:', url, flush=True)
for i in range(34):
    time.sleep(15)
    g = requests.get('https://api.vercel.com/v13/deployments/' + did, headers=H, timeout=30).json()
    st = g.get('state') or g.get('status')
    print('[%d] %s' % (i, st), flush=True)
    if st == 'READY':
        print('FINAL-URL:', url, flush=True)
        break
    if st in ('ERROR', 'CANCELED'):
        print(str(g)[:900], flush=True)
        break
