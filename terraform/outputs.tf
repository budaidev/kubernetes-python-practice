data "kubernetes_service" "app" {
  metadata {
    name      = "${var.app_name}-service"
    namespace = var.namespace
  }
  depends_on = [helm_release.python_webapp]
}

output "app_url" {
  description = "Application URL"
  value       = "http://localhost:${data.kubernetes_service.app.spec.0.port.0.port}"
}

output "namespace" {
  description = "Kubernetes namespace"
  value       = var.namespace
}

output "helm_release_name" {
  description = "Helm release name"
  value       = helm_release.python_webapp.name
}

output "minikube_url" {
  description = "Minikube service URL"
  value       = "Run: minikube service ${var.app_name}-service -n ${var.namespace}"
}