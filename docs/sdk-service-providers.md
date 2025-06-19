Python SDK for Service Providers to validate Agent Identity Framework (AIF) tokens issued by Heimdall-compliant Issuing Entities. Verify agent tokens with cryptographic signature validation, audience checking, and revocation status - ensuring only authorized AI agents can access your services.

## Installation

```bash
pip install heimdall-sp-validator-sdk
```

## Quick Start

```python
from heimdall_sp_validator_sdk import AIFTokenValidator, AIFValidatorConfig

# Configure validator
config = AIFValidatorConfig(
    aif_core_service_url="https://poc.iamheimdall.com",
    expected_sp_audiences=["my-service-api"],
    expected_issuer_id="aif://poc-heimdall.example.com"
)

validator = AIFTokenValidator(config)

# Validate token
try:
    result = await validator.verify_atk(token_string)
    print(f"Valid token for user: {result.user_id_from_aid}")
    print(f"Permissions: {result.permissions}")
except Exception as e:
    print(f"Invalid token: {e}")
```

## Configuration

### Environment Variables (Recommended)

Copy `.env.example` to `.env` and configure:

```bash
AIF_CORE_SERVICE_URL=https://poc.iamheimdall.com
AIF_EXPECTED_ISSUER_ID=aif://poc-heimdall.example.com
AIF_SP_EXPECTED_AUDIENCES=my-service-api,another-service
```

Use environment-based configuration:

```python
config = AIFValidatorConfig.from_env()
validator = AIFTokenValidator(config)
```

### Configuration Options

| Parameter | Default | Description |
|-----------|---------|-------------|
| `aif_core_service_url` | Required | Base URL of AIF core service |
| `expected_sp_audiences` | Required | Your service audience ID(s) |
| `expected_issuer_id` | Required | Trusted issuer identifier |
| `jwks_cache_ttl_seconds` | 86400 | JWKS cache duration (24 hours) |
| `revocation_check_enabled` | true | Enable revocation checking |
| `revocation_check_timeout_seconds` | 5 | Revocation check timeout |
| `clock_skew_seconds` | 60 | Allowed time skew for validation |

## Full Documentation & Examples

For complete documentation, advanced configuration, integration examples, and troubleshooting:

**[View Full Documentation on GitHub](https://github.com/IAM-Heimdall/heimdall-sp-validator-sdk-python)**

## License

[MIT License](https://github.com/IAM-Heimdall/heimdall-sp-validator-sdk-python/blob/main/LICENSE)