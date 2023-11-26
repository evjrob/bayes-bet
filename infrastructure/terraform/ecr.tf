resource "aws_ecr_repository" "bayesbet_model_ecr" {
  name                 = "${var.project}-model-${var.env}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

resource "aws_ecr_repository" "bayesbet_social_ecr" {
  name                 = "${var.project}-social-${var.env}"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

