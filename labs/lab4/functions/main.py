
import pandas as pd
import functions_framework

@functions_framework.http
def read_csv_and_print_info(request):
    # URL of the CSV file
    csv_url = "https://vincentarelbundock.github.io/Rdatasets/csv/ggplot2/diamonds.csv"
    
    try:
        # Read the CSV file from the web
        df = pd.read_csv(csv_url)
        
        # Capture the info output as a string
        info_string = df.info(buf=None, max_cols=None, memory_usage=False)
        
        # Print the info (this will be logged in Cloud Functions)
        print(info_string)
        
        return f"CSV file processed successfully. Info printed to logs."
    
    except Exception as e:
        error_message = f"An error occurred: {str(e)}"
        print(error_message)
        return error_message
        