resource "aws_sns_topic" "this" {
  name         = "${var.topic_name}-${var.environment}"
  display_name = var.display_name
}

# SNS Topic Policy
resource "aws_sns_topic_policy" "this" {
  arn    = aws_sns_topic.this.arn
  policy = data.aws_iam_policy_document.sns_topic_policy.json
}

data "aws_iam_policy_document" "sns_topic_policy" {
  statement {
    sid    = "AllowPublishToSNS"
    effect = "Allow"
    
    principals {
      type        = "AWS"
      identifiers = var.publisher_principals
    }
    
    actions = [
      "sns:Publish",
      "sns:GetTopicAttributes",
    ]
    
    resources = [
      aws_sns_topic.this.arn,
    ]
  }
}