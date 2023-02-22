variable attributes {
  type        = list(map(string))
  description = "Please provide the attributes list for the keys"
  default     = []
}

variable autoscaling_enabled {
  type        = bool
  description = "Please provide if autoscaling is enabled"
  default     = false
}

variable create_table {
  type        = bool
  description = "Please provide if table should be created"
  default     = false
}

variable hash_key {
  type        = string
  description = "Please provide the hash key for table"
}

variable range_key {
  type        = string
  description = "Please provide the range key for table"
  default     = null
}

variable table_class {
  type        = string
  description = "Please provide table_class"
  default     = "STANDARD"
}

variable table_name {
  type        = string
  description = "Please provide name for dynamo table"
}

variable tags {
    type      = map(string)
}
