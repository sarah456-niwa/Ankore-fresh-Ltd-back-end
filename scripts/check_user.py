import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','ankore.settings')
import django
django.setup()
from users.models import User
email='snuwahereza0@gmail.com'
try:
    u=User.objects.get(email=email)
    print('FOUND', u.email, 'id', u.id)
    print('password field:', u.password)
    print('check_password("1432567n") ->', u.check_password('1432567n'))
    print('username:', u.username)
    print('date_joined:', getattr(u,'date_joined',None))
except Exception as e:
    print('ERR', e)
