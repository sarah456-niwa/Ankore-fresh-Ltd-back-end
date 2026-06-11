import requests

LOGIN_URL = 'http://127.0.0.1:8000/api/auth/mobile-login/'
FAV_URL = 'http://127.0.0.1:8000/api/auth/favorites/'

email = 'snuwahereza0@gmail.com'
password = 'newpass123'  # after change

r = requests.post(LOGIN_URL, json={'email': email, 'password': password})
print('login', r.status_code, r.text)
if r.status_code == 200:
    access = r.json().get('access')
    headers = {'Authorization': f'Bearer {access}', 'Content-Type': 'application/json'}
    # Add favorite
    p = requests.post(FAV_URL, json={'product_id': 'prod_1'}, headers=headers)
    print('post fav', p.status_code, p.text)
    # Get favorites
    g = requests.get(FAV_URL, headers=headers)
    print('get favs', g.status_code, g.text)
    # Delete favorite
    d = requests.delete(FAV_URL + 'prod_1/', headers=headers)
    print('delete fav', d.status_code, d.text)
    # Get again
    g2 = requests.get(FAV_URL, headers=headers)
    print('get favs after', g2.status_code, g2.text)
else:
    print('login failed')
