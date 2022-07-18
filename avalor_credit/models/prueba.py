import json
import requests
from requests.structures import CaseInsensitiveDict

url = "https://testapi-gw.payclip.com/loans/preapproval/ff9b055a-ec9d-4aef-af8a-be5741831c61"

headers = CaseInsensitiveDict()
headers["Accept"] = "application/json"
headers["x-api-key"] = "kg6zvEiihZ7vY0R4Kf9cD6anEZymia2MaLM8ihkW"
headers["Content-Type"] = "application/json"

data ={
  "status": "IN_ANALYSIS",
  "detail": "",
  "date": "2022-04-28T12:30:00Z"
}



resp = requests.patch(url, headers=headers, data=json.dumps(data))

print(resp.status_code)
print(resp.text)
print(resp.headers)


