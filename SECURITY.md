# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security issue, please report it responsibly.

### How to Report

**Please do NOT report security vulnerabilities through public GitHub issues.**

Instead, please report them via one of the following methods:

1. **GitHub Security Advisories** (Preferred): Use [GitHub's private vulnerability reporting](../../security/advisories/new) to submit a report directly through the repository.

2. **Email**: Send details to the repository maintainers (check the repository for contact information).

### What to Include

When reporting a vulnerability, please include:

- **Description**: A clear description of the vulnerability
- **Impact**: The potential impact and severity
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Affected Versions**: Which versions are affected
- **Proof of Concept**: If possible, provide a minimal proof of concept
- **Suggested Fix**: If you have suggestions for how to fix the issue

### Response Timeline

- **Initial Response**: We aim to acknowledge receipt within 48 hours
- **Status Update**: We will provide a status update within 7 days
- **Resolution**: We aim to resolve critical vulnerabilities within 30 days

### Disclosure Policy

- We follow coordinated disclosure practices
- We will work with you to understand and resolve the issue
- We will credit reporters in the security advisory (unless you prefer to remain anonymous)
- We request that you do not publicly disclose the issue until we have had a chance to address it

## Security Considerations for This Project

### Hardware Communication

TinySA Coordinator communicates with TinySA Ultra devices via USB serial connections. Security considerations include:

- **Local Access Only**: Serial communication is inherently local; the device must be physically connected
- **No Remote Device Access**: The application does not expose device control over the network beyond the local API
- **Input Validation**: All serial commands are validated before transmission to the device

### Network Security

- **Local Development**: By default, the application runs on localhost and is not exposed to external networks
- **WebSocket Security**: WebSocket connections are used for real-time data streaming; ensure proper authentication if deploying beyond localhost
- **API Security**: When deploying to production, implement appropriate authentication and authorization mechanisms

### Data Storage

- **SQLite Database**: Scan history is stored locally in SQLite (`data/scanner.db`)
- **No Sensitive Data**: The application does not store passwords, API keys, or other sensitive credentials by default
- **File Permissions**: Ensure appropriate file permissions on the database and configuration files

### Docker Deployment

When running in Docker:

- Use official base images and keep them updated
- Do not run containers as root in production
- Limit container capabilities and resources
- Use secrets management for any sensitive configuration

### Dependency Security

- **Dependabot**: This repository uses Dependabot for automated dependency updates
- **Regular Updates**: We recommend keeping all dependencies up to date
- **Vulnerability Scanning**: Review dependency vulnerabilities through GitHub's security features

## Security Best Practices for Users

1. **Keep Updated**: Always use the latest stable version
2. **Network Isolation**: If deploying beyond localhost, ensure proper network security measures
3. **Access Control**: Implement authentication if the application is accessible to multiple users
4. **Regular Backups**: Back up your scan history database if the data is important
5. **Monitor Dependencies**: Enable Dependabot alerts for your fork

## Acknowledgments

We appreciate the security research community and thank all individuals who responsibly disclose vulnerabilities.
