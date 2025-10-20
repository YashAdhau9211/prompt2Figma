# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Which versions are eligible for receiving such patches depends on the CVSS v3.0 Rating:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to [security@prompt2figma.com](mailto:security@prompt2figma.com).

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the following information in your report:

* Type of issue (e.g. buffer overflow, SQL injection, cross-site scripting, etc.)
* Full paths of source file(s) related to the manifestation of the issue
* The location of the affected source code (tag/branch/commit or direct URL)
* Any special configuration required to reproduce the issue
* Step-by-step instructions to reproduce the issue
* Proof-of-concept or exploit code (if possible)
* Impact of the issue, including how an attacker might exploit it

This information will help us triage your report more quickly.

## Preferred Languages

We prefer all communications to be in English.

## Security Update Process

1. **Report Received**: Security team acknowledges receipt within 48 hours
2. **Triage**: Team assesses severity and impact (1-3 business days)
3. **Fix Development**: Patch is developed and tested
4. **Disclosure**: Security advisory is published
5. **Release**: Patched version is released

## Security Best Practices

When using Prompt2Figma, please follow these security best practices:

### For Users

1. **Keep Updated**: Always use the latest version
2. **Secure API Keys**: Never commit API keys to version control
3. **Environment Variables**: Use `.env` files for sensitive data
4. **Rate Limiting**: Respect rate limits to prevent abuse
5. **Input Validation**: Be cautious with user-generated content

### For Contributors

1. **Code Review**: All code must be reviewed before merging
2. **Dependency Scanning**: Regularly update and scan dependencies
3. **Input Sanitization**: Always sanitize user input
4. **Authentication**: Use secure authentication methods
5. **Encryption**: Encrypt sensitive data in transit and at rest

## Known Security Considerations

### Input Sanitization

The application implements comprehensive input sanitization to prevent:
- SQL Injection
- XSS (Cross-Site Scripting)
- Command Injection
- Path Traversal

### Rate Limiting

Rate limits are enforced at multiple levels:
- Per minute: 10 requests
- Per hour: 100 requests
- Per day: 500 requests

### Session Security

- Cryptographically secure session IDs (128-bit)
- Session expiration after 24 hours of inactivity
- Secure session storage in Redis

### API Security

- Input validation on all endpoints
- CORS configuration
- Request size limits
- Timeout protection

## Security Audit History

| Date | Auditor | Findings | Status |
|------|---------|----------|--------|
| TBD  | TBD     | TBD      | TBD    |

## Disclosure Policy

When we receive a security bug report, we will:

1. Confirm the problem and determine affected versions
2. Audit code to find any similar problems
3. Prepare fixes for all supported versions
4. Release new versions as soon as possible

## Comments on this Policy

If you have suggestions on how this process could be improved, please submit a pull request or open an issue to discuss.

## Hall of Fame

We recognize security researchers who responsibly disclose vulnerabilities:

<!-- Add contributors here -->
- TBD

Thank you for helping keep Prompt2Figma and our users safe!
