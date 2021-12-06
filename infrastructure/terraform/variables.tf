variable "project" {
  default = "bayesbet"
  type    = string
}

variable "env" {
  default = "dev"
  type    = string
}

variable "scheduled" {
  default = false
  type    = bool
}