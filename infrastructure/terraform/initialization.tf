resource "random_id" "image_tag" {
  keepers = {
    uuid = uuid()
  }
  
  byte_length = 4
}


resource "null_resource" "ecr_docker_image" {
  provisioner "local-exec" {
    command = "/bin/bash assets/deploy_image.sh ${aws_ecr_repository.bayesbet_model_ecr.repository_url} ${random_id.image_tag.hex}"
  }

  triggers = {
    always_run = "${timestamp()}"
  }
  
  depends_on = [
    aws_ecr_repository.bayesbet_model_ecr,
  ]

}
