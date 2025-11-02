resource "google_project_service" "required" {
  for_each = toset(var.apis)
  project  = var.project_id
  service  = each.key
}
