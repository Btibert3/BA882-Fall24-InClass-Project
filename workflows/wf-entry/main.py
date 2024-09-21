# basic entry point for workflow - returns two ids from MD

# imports
import functions_framework

@functions_framework.http
def main(request):
    
    return {
        "statusCode":200, 
        "ids":[{'id':'409b79b6115c8d051434bfcecf60f69c9f2965e0'}, 
               {'id':'b3651fff16e6104442c8f66f8d99aa2545a4c7d8'}]
    }
