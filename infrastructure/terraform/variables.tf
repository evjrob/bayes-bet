variable "project" {
  default = "bayes-bet"
  type    = string
}

variable "env" {
  default = "dev"
  type    = string
}

variable "socials_scheduled" {
  default = false
  type    = bool
}

variable "socials_url" {
  default = ""
  type    = string
}

variable "twitter_bearer_token" {
  default   = ""
  type      = string
  sensitive = true
}

variable "twitter_consumer_key" {
  default   = ""
  type      = string
  sensitive = true
}

variable "twitter_consumer_secret" {
  default   = ""
  type      = string
  sensitive = true
}

variable "twitter_access_token" {
  default   = ""
  type      = string
  sensitive = true
}

variable "twitter_access_token_secret" {
  default   = ""
  type      = string
  sensitive = true
}

variable "deployment_version" {
  default   = ""
  type      = string
  sensitive = true
}