output "ecr_rpc_id" {
  value = aws_ecr_repository.ecr_rpc.id
}

output "ecr_rpc_arn" {
  value = aws_ecr_repository.ecr_rpc.arn
}

output "ecr_rpc_url" {
  value = aws_ecr_repository.ecr_rpc.repository_url
}

output "ecr_worker_id" {
  value = aws_ecr_repository.ecr_worker.id
}

output "ecr_worker_arn" {
  value = aws_ecr_repository.ecr_worker.arn
}

output "ecr_worker_url" {
  value = aws_ecr_repository.ecr_worker.repository_url
}

output "ecr_rpc_repository_name" {
  value = aws_ecr_repository.ecr_rpc.name
}

output "ecr_worker_repository_name" {
  value = aws_ecr_repository.ecr_worker.name
}
