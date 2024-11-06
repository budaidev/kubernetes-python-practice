variable "minikube_context" {
  description = "Minikube context name"
  type        = string
  default     = "minikube"
}

variable "namespace" {
  description = "Kubernetes namespace"
  type        = string
  default     = "default"
}

variable "app_name" {
  description = "Application name"
  type        = string
  default     = "python-webapp"
}

variable "replica_count" {
  description = "Number of replicas"
  type        = number
  default     = 1
}

variable "image_repository" {
  description = "Docker image repository"
  type        = string
  default     = "python-webapp"
}

variable "image_tag" {
  description = "Docker image tag"
  type        = string
  default     = "latest"
}
