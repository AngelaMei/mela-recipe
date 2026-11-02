# Build both Mela images with Docker Buildx (in parallel).
#
#   docker buildx bake --push                          # REGISTRY and TAG from the environment
#   REGISTRY=ghcr.io/you TAG=abc123 docker buildx bake --push
#   docker buildx bake --load api                      # one image, into the local Docker
#
# deploy/deploy.sh calls this with TAG set to the git commit.

variable "REGISTRY" {
  default = "mela"
}

variable "TAG" {
  default = "dev"
}

variable "PLATFORM" {
  default = "linux/amd64"
}

group "default" {
  targets = ["api", "web"]
}

target "_common" {
  platforms = ["${PLATFORM}"]
  labels = {
    "org.opencontainers.image.source"   = "https://github.com/AngelaMei/mela-recipe"
    "org.opencontainers.image.revision" = "${TAG}"
  }
}

target "api" {
  inherits = ["_common"]
  context  = "backend"
  tags     = ["${REGISTRY}/mela-api:${TAG}"]
}

target "web" {
  inherits = ["_common"]
  context  = "web"
  args = {
    API_INTERNAL_URL = "http://mela-api:8000"
  }
  tags = ["${REGISTRY}/mela-web:${TAG}"]
}
