import requests
import functions_framework

@functions_framework.http
def app(request):
    # URL of a service to get information on fruits
    url = "https://www.fruityvice.com/api/fruit/all"
    
    try:
        resp = requests.get(url)
        fruits = resp.json()

        return fruits, 200
    
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        return error_message
        