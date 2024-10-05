variable "project_id" {
  description = "The GCP project ID where the resources will be created"
  type        = string
  default     = "btibert-ba882-fall24"
}

variable "region" {
  description = "The GCP region for the Cloud Function"
  type        = string
  default     = "us-central1"  # Adjust based on your preferred region
}
