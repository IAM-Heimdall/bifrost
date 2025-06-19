# Bifrost - Core Service

## Overview

This repository contains the first version of a combined **Issuing Entity (IE)** and **Registry (REG)** service, providing a complete proof-of-concept implementation of agent identity management.

## Architecture

Bifrost implements two core AIF components in a single service:

- **Issuing Entity (IE)**: Issues and signs Agent Tokens (ATKs) for AI agents
- **Registry (REG)**: Provides public key discovery (JWKS) and manages token revocation

## Key Features

### Token Management
- **EdDSA/Ed25519 Cryptography**: Modern, secure digital signatures
- **JWT-based Agent Tokens**: Standards-compliant token format
- **Trust Tags**: Metadata for agent assurance and environment context
- **Configurable Permissions**: Flexible permission model for service access

### Security & Reliability
- **Token Revocation**: Real-time revocation status checking
- **JWKS Endpoint**: Standard key discovery for service providers
- **Database Integration**: Persistent storage for revocation lists

### User Experience
- **Web Management UI**: Simple interface for token operations
- **RESTful APIs**: Complete API coverage for programmatic access
- **Real-time Feedback**: Detailed logging and status reporting

### SDK and Documentation
- **Agent Creator SDK**: Create and Revoke tokens. Helper functions to build httpx headers.
- **Service Provider SDK**: Extract and Verify tokens. Check for revocation status.
- **Documentation**: API Reference, Documentation for SDKs and Whitepaper.


## Links

- **Documentation**: [Documentation](https://poc.iamheimdall.com/ui/api-reference)
- **Website**: [Website](iamheimdall.com)


---

*Named after the rainbow bridge of Norse mythology, Bifrost connects the realms of AI agents and digital services, enabling secure, verifiable interactions in the Agent Identity Framework.*