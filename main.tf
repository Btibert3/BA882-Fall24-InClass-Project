provider "google" {
  project = var.project_id
  region  = var.region
}


# Automatically zip the Cloud Function's Python code
data "archive_file" "cloud_function_zip" {
  type        = "zip"
  source_dir  = "${path.root}/labs/lab6/"  # Directory with main.py and requirements.txt
  output_path = "${path.module}/cloud_function.zip"
}

# Upload the zip file to the pre-existing GCS bucket
resource "google_storage_bucket_object" "cloud_function_code" {
  name   = "cloud_function.zip"  # Name of the object in GCS
  bucket = "btibert-ba882-fall24-functions"  # Replace with the name of your GCS bucket
  source = data.archive_file.cloud_function_zip.output_path
}

# Deploy the Cloud Function
resource "google_cloudfunctions_function" "function" {
  name        = "lab6-terraform"
  description = "A sample Cloud Function deployed via Terraform"
  runtime     = "python311"
  region      = var.region
  entry_point = "app"

  available_memory_mb   = 128
  service_account_email = "etl-pipeline@btibert-ba882-fall24.iam.gserviceaccount.com"  # Your service account
  source_archive_bucket = "btibert-ba882-fall24-functions"  # Replace with your pre-existing GCS bucket for cloud functions
  source_archive_object = google_storage_bucket_object.cloud_function_code.name  # The uploaded zip file

  trigger_http = true
  https_trigger_security_level = "SECURE_ALWAYS"

  environment_variables = {
    FUNCTION_ENV = "dev"
  }
}

# Output the URL of the Cloud Function
output "cloud_function_url" {
  value = google_cloudfunctions_function.function.https_trigger_url
}