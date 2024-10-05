terraform {
  backend "gcs" {
    bucket = "btibert-ba882-fall24-terraform"
    prefix = "terraform/state"
  }
}
