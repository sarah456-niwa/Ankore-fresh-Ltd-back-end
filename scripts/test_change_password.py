import requests

LOGIN_URL = 'http://127.0.0.1:8000/api/auth/mobile-login/'
CHANGE_URL = 'http://127.0.0.1:8000/api/auth/password/change/'

email = 'snuwahereza0@gmail.com'
old = '1432567n'
new = 'newpass123'

r = requests.post(LOGIN_URL, json={'email': email, 'password': old})
print('login', r.status_code, r.text)
if r.status_code == 200:
    access = r.json().get('access')
    headers = {'Authorization': f'Bearer {access}', 'Content-Type': 'application/json'}
    c = requests.post(CHANGE_URL, json={'old_password': old, 'new_password': new}, headers=headers)
    print('change', c.status_code, c.text)
else:
    print('login failed')
