# HTTP API + routes to Lambdas.
#
#   POST /orders       → careplan-create-order
#   GET  /orders/{id}  → careplan-get-order
#
# generate_careplan stays SQS-triggered (see wiring.tf), not on API Gateway.

resource "aws_apigatewayv2_api" "careplan" {
  name          = "careplan-practice-api"
  protocol_type = "HTTP"
  description   = "CarePlan practice HTTP API"

  tags = {
    Project = "CarePlan"
    Purpose = "terraform-apigw-exercise"
  }
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.careplan.id
  name        = "$default"
  auto_deploy = true

  tags = {
    Project = "CarePlan"
    Purpose = "terraform-apigw-exercise"
  }
}

# ----- Integrations (API Gateway → Lambda, proxy mode) -----

resource "aws_apigatewayv2_integration" "create_order" {
  api_id                 = aws_apigatewayv2_api.careplan.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.create_order.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_integration" "get_order" {
  api_id                 = aws_apigatewayv2_api.careplan.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.get_order.invoke_arn
  integration_method     = "POST"
  payload_format_version = "2.0"
}

# ----- Routes -----

resource "aws_apigatewayv2_route" "post_orders" {
  api_id    = aws_apigatewayv2_api.careplan.id
  route_key = "POST /orders"
  target    = "integrations/${aws_apigatewayv2_integration.create_order.id}"
}

resource "aws_apigatewayv2_route" "get_order" {
  api_id    = aws_apigatewayv2_api.careplan.id
  route_key = "GET /orders/{id}"
  target    = "integrations/${aws_apigatewayv2_integration.get_order.id}"
}

# ----- Permission: allow API Gateway to invoke each Lambda -----

resource "aws_lambda_permission" "apigw_invoke_create_order" {
  statement_id  = "AllowAPIGatewayInvokeCreateOrder"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.create_order.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.careplan.execution_arn}/*/*/orders"
}

resource "aws_lambda_permission" "apigw_invoke_get_order" {
  statement_id  = "AllowAPIGatewayInvokeGetOrder"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_order.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.careplan.execution_arn}/*/*/orders/*"
}

output "api_gateway_id" {
  value = aws_apigatewayv2_api.careplan.id
}

output "api_gateway_endpoint" {
  description = "Base URL, e.g. https://xxxx.execute-api.us-east-1.amazonaws.com"
  value       = aws_apigatewayv2_api.careplan.api_endpoint
}

output "api_gateway_arn" {
  value = aws_apigatewayv2_api.careplan.arn
}

output "api_post_orders_url" {
  value = "${aws_apigatewayv2_api.careplan.api_endpoint}/orders"
}

output "api_get_order_url_example" {
  value = "${aws_apigatewayv2_api.careplan.api_endpoint}/orders/{id}"
}
