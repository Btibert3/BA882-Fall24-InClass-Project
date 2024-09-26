import subprocess
import os
from flask import Flask, request, jsonify
from google.cloud import storage

app = Flask(__name__)

# Function to upload file to GCS
def upload_to_gcs(bucket_name, source_file, destination_blob):
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob)
    blob.upload_from_filename(source_file)
    print(f"File {source_file} uploaded to {destination_blob}.")

# Function to render Quarto report
def render_quarto_report(year):
    # Path to your Quarto template
    report_template = "template.qmd"
    
    # Render the report with passed parameters
    output_filename = f"report_{year}.html"
    subprocess.run([
        "quarto", "render", report_template,
        "-P", f"year:{year}",
        "-o", output_filename
    ])
    
    print(f"returning the filename: {output_filename}")
    return output_filename

@app.route('/', methods=['POST'])
def main():
    try:
        # Parse request JSON
        data = request.json
        year = data.get('year')

        # Render the Quarto report
        output_file = render_quarto_report(year)
        print("file was rendered, moving onto move to GCS")
        print(f"File is: {output_file}")

        # Upload to GCS
        bucket_name = "btibert-ba882fall24-reports"
        gcs_destination = f"reports/{output_file}"
        upload_to_gcs(bucket_name, output_file, gcs_destination)

        return jsonify({"message": "Report generated", "gcs_file": gcs_destination}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
