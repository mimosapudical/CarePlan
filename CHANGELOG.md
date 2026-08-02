# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.7.0] — 2026-08-03

### Added

- Terraform infrastructure under `infra/practice/` (API Gateway, Lambda, SQS + DLQ, RDS)
- Infrastructure as Code deployment path for a short-lived AWS practice stack
- Project documentation: architecture, deployment, tradeoffs, Day 15 engineering notes

### Changed

- Deployment process for cloud practice resources migrated from manual AWS console setup to Terraform

### Notes

- Cloud resources are created only for testing and destroyed afterward (`terraform destroy`) to minimize AWS costs

[0.7.0]: docs/releases/v0.7.md
