import requests
import json

station_ids = [
    '1611400','1612340','1612401','1612480','1615680','1617433','1617760',
    '1619910','1630000','1631428','1770000','1820000','1890000'
]

results = {}
for sid in station_ids:
    url = f'https://api.tidesandcurrents.noaa.gov/mdapi/prod/webapi/stations/{sid}.json'
    r = requests.get(url)
    j = r.json()
    station = j.get('stations', [{}])[0]
    results[sid] = {
        'name': station.get('name'),
        'lat': station.get('lat'),
        'lng': station.get('lng'),
        'state': station.get('state'),
        'type': station.get('type')
    }
    print(f"{sid}: {results[sid]}")

with open('station_metadata.json', 'w') as f:
    json.dump(results, f, indent=2)
