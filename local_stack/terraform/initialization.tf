resource "null_resource" "s3_initialization" {
  provisioner "local-exec" {
    command = "aws --endpoint=http://localhost:4566 s3 cp assets/pred_dates.json s3://${aws_s3_bucket.bayesbet_web_bucket.id}/pred_dates.json"
  }
  depends_on = [
    aws_s3_bucket.bayesbet_web_bucket,
  ]
}

resource "null_resource" "dynamodb_initialization" {
  provisioner "local-exec" {
    command = "aws --endpoint=http://localhost:4566 dynamodb put-item --table-name ${aws_dynamodb_table.bayesbet_games.name} --item file://assets/db_item.json"
  }
  depends_on = [
    aws_dynamodb_table.bayesbet_games,
  ]
}
