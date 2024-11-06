provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "minikube"
}

provider "helm" {
  kubernetes {
    config_path    = "~/.kube/config"
    config_context = "minikube"
  }
}

# Only create namespace if it's not "default"
resource "kubernetes_namespace" "app" {
  count = var.namespace != "default" ? 1 : 0

  metadata {
    name = var.namespace
  }
}

resource "helm_release" "python_webapp" {
  name       = var.app_name
  chart      = "../helm/python-webapp"
  namespace  = var.namespace

  # Add force_update and replace settings
  force_update  = true
  replace       = true
  recreate_pods = true

  set {
    name  = "namespace"
    value = var.namespace
  }

  set {
    name  = "replicaCount"
    value = var.replica_count
  }

  set {
    name  = "image.repository"
    value = var.image_repository
  }

  set {
    name  = "image.tag"
    value = var.image_tag
  }

  depends_on = [kubernetes_namespace.app]
}