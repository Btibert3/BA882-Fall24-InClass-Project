import requests

url = "https://quarto-render-service-1077323016672.us-central1.run.app"

# test the url
payload = {
    "year":2040
}
resp = requests.post(url, json=payload)

resp.status_code