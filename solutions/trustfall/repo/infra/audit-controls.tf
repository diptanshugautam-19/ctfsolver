resource "aws_kms_key" "legacy_exports" {
  description         = "Legacy export encryption"
  enable_key_rotation = true
}

resource "aws_kms_key" "archive" {
  description         = "Archive export encryption"
  enable_key_rotation = false
}

resource "aws_s3_bucket_server_side_encryption_configuration" "legacy_exports" {
  bucket = aws_s3_bucket.legacy_exports.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.legacy_exports.arn
    }
  }
}

resource "aws_s3_bucket_versioning" "legacy_exports" {
  bucket = aws_s3_bucket.legacy_exports.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_public_access_block" "legacy_exports" {
  bucket                  = aws_s3_bucket.legacy_exports.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
