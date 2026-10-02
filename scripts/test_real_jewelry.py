import requests
import json

s = requests.Session()
reg = s.post('http://127.0.0.1:8000/register', data={
    'full_name': 'Gold Test',
    'username': 'gold_tester_42',
    'email': 'gold42@example.com',
    'password': 'password123'
})
print('Register status:', reg.status_code)

res = s.post('http://127.0.0.1:8000/generate-jewelry', data={
    'total_budget': 35000,
    'occasion': 'Wedding / Reception',
    'style_preference': 'Traditional Temple & Heritage',
    'precious_metal': 'Gold',
    'location': 'Chennai'
}, headers={'accept': 'application/json'})
print('Jewelry status:', res.status_code)
data = res.json()
summary = data['summary']
print('Total budget:', summary['total_budget'])
print('Total spend:', summary['total_spend'])
print('Items count:', len(summary['items']))
for it in summary['items']:
    print(f"[{it['category']}] {it['name']} -> Brand: {it['platform']}, Badge: {it.get('purity_badge')}, Price: {it['total_price']}")

shops = summary.get('nearby_shops') or []
print('Nearby shops count:', len(shops))
for sh in shops[:3]:
    print(f"Showroom: {sh['full_name']} -> Maps: {sh['maps_url']}")
