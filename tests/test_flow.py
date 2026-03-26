import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from products.models import Product

@pytest.mark.django_db
def test_full_order_flow(client):
    User = get_user_model()
    resp = client.post(reverse('register'), data={'username':'u1','email':'u1@e.com','password':'Password123!'})
    assert resp.status_code == 201
    resp = client.post(reverse('login'), data={'username':'u1','password':'Password123!'})
    assert resp.status_code == 200
    access = resp.json()['access']
    auth = {'HTTP_AUTHORIZATION': f'Bearer {access}'}
    resp = client.post(reverse('top_up'), data={'amount':'100.00'}, **auth)
    assert resp.status_code == 200
    u = User.objects.get(username='u1'); u.is_staff=True; u.save()
    resp = client.post('/api/products/', data={'name':'P1','price':'10.00','stock':5}, **auth)
    assert resp.status_code == 201
    pid = resp.json()['id']
    resp = client.post('/api/cart/items/', data={'product_id': pid, 'quantity': 2}, **auth)
    assert resp.status_code == 201
    resp = client.post('/api/orders/create-from-cart/', **auth)
    assert resp.status_code == 201
    data = resp.json()
    assert data['total'] == '20.00'
    resp = client.get('/api/cart/items/', **auth)
    assert resp.status_code == 200
    assert resp.json()['items'] == []
