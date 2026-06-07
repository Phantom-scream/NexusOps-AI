resource "kubernetes_deployment" "checkout" {
  metadata {
    name = "checkout-api"
  }

  spec {
    replicas = 3
    template {
      spec {
        container {
          name  = "checkout"
          image = "checkout:latest"
          security_context {
            privileged  = true
            run_as_user = 0
          }
        }
      }
    }
  }
}

resource "kubernetes_cluster_role" "wildcard_operator" {
  metadata {
    name = "wildcard-operator"
  }

  rule {
    api_groups = ["*"]
    resources  = ["*"]
    verbs      = ["*"]
  }
}
