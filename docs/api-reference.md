**Version:** v0.4  
**Base URL:** Current website instance

## Authentication

Most endpoints require Bearer token authentication. Agent Builders can generate API tokens through the dashboard after signing up. Currently GitHub oauth is supported.

```http
Authorization: Bearer YOUR_API_TOKEN
```

## Registry and Issuing Entity

**Registry (REG):** Public endpoints for Service Providers to validate Agent Tokens and check revocation status.
**Issuing Entity (IE):** Authenticated endpoints for Agent Builders to issue and manage Agent Tokens (ATKs).

---
## For Service Providers

Service Providers are publishers, SaaS platforms, API providers, and product builders who need to verify AI agent identities. The Registry provides public endpoints to validate Agent Tokens without requiring authentication.

### Get Public Keys (JWKS)

Retrieve the public keys needed to verify Agent Token signatures.

**What is it for?** Service Providers use these keys to cryptographically verify that incoming Agent Tokens are authentic and haven't been tampered with.

```http
GET /.well-known/jwks.json
```

**Response:**
```json
{
  "keys": [
    {
      "kty": "OKP",
      "crv": "Ed25519",
      "kid": "poc-heimdall-key-01",
      "x": "base64url-encoded-public-key",
      "alg": "EdDSA",
      "use": "sig"
    }
  ]
}
```

**Usage:** Cache this response and refresh periodically. Use the public key to verify JWT signatures using standard JWT libraries.

### Check Token Revocation Status

Verify if a specific Agent Token has been revoked.

```http
GET /reg/revocation-status?jti={token_id}
```

**Parameters:**
- `jti` (required) - The JWT ID from the Agent Token

**Response:**
```json
{
  "jti": "unique-token-id",
  "is_revoked": false,
  "checked_at": "2025-01-15T10:30:00Z"
}
```

**Error Codes:**
- `400` - Invalid or missing JTI
- `500` - Server error during lookup

**Usage:** Check revocation status for high-security operations or when caching tokens for extended periods.

### Service Provider SDK

Verify agent tokens with cryptographic signature validation, audience checking, and revocation status - ensuring only authorized AI agents can access your services.

**Installation**

```bash
pip install heimdall-sp-validator-sdk
```

And, follow further steps from sdk documentation

---
## For Agent Builders

Agent Builders are developers creating AI agents that need authenticated access to external services.

### Getting Authentication Token

1. **Sign In:** Log in through GitHub OAuth using the "Sign up with GitHub" button
2. **Generate Token:** Navigate to your dashboard and click "Generate new token"
3. **Secure Storage:** Copy and securely store your API token - you won't see it again

**Token Security:** Never expose API tokens in client-side code. Store securely in environment variables or secure configuration.

### Issue Agent Token (ATK)

Create a new Agent Token for your AI agent to access a specific service.

```http
POST /api/v1/ie/issue-atk
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
```

**Request:**
```json
{
  "user_id": "end-user-123",
  "audience_sp_id": "https://api.newsservice.com",
  "permissions": ["read:articles_all", "summarize:text_content_short"],
  "purpose": "Daily news summary for user dashboard",
  "model_id": "gpt-4-turbo"
}
```

**Parameters:**
- `user_id` - Identifier for the user delegating the agent
- `audience_sp_id` - Target service provider's API endpoint
- `permissions` - Array of specific permissions needed
- `purpose` - Human-readable description of the agent's task
- `model_id` - AI model being used

**Response:**
```json
{
  "atk": "eyJhbGciOiJFZERTQSIsImtpZCI6InBvYy1oZWltZGFsbC1rZXktMDEiLCJ0eXAiOiJKV1QifQ..."
}
```

**Error Codes:**
- `400` - Invalid parameters or unsupported model/permissions
- `401` - Missing or invalid API token
- `500` - Token generation failed

**Token Lifetime:** Tokens expire after 15 minutes by default. Issue new tokens as needed.

### Revoke Agent Token

Immediately invalidate a previously issued Agent Token.

```http
POST /reg/revoke-atk
Authorization: Bearer YOUR_API_TOKEN
Content-Type: application/json
```

**Request:**
```json
{
  "jti": "token-id-to-revoke"
}
```

**Response:**
```json
{
  "message": "Token 'token-id-to-revoke' successfully revoked"
}
```

**Error Codes:**
- `400` - Invalid JTI format
- `401` - Authentication required
- `403` - Can only revoke tokens you issued
- `500` - Revocation failed

**Security:** You can only revoke tokens that you originally issued. This prevents unauthorized revocation of other users' tokens.

### Agent Builder SDK
Issue and manage Agent Tokens (ATKs) to enable your AI agents to authenticate securely with service providers.

**Installation**

```bash
pip install heimdall-agent-builder-sdk
```
---

## Security Considerations

### For Service Providers

**Token Validation Pipeline:**
1. Verify JWT signature using JWKS public keys
2. Check token expiration (`exp` claim)
3. Validate audience matches your service (`aud` claim)
4. For sensitive operations, check revocation status
5. Enforce permissions based on your service requirements

**Implementation:**
```bash
# 1. Get public keys (cache this)
curl "/.well-known/jwks.json"

# 2. Check revocation (optional, for high-security use)
curl "/reg/revocation-status?jti=token-jti"

# 3. Validate signature in your application code
```

### For Agent Builders

**API Token Security:**
- Store tokens in environment variables, never in code
- Use HTTPS for all API calls
- Regenerate tokens if compromised
- Set up token rotation policies

**Token Management:**
- Request minimal permissions needed
- Use descriptive purposes for audit trails
- Revoke tokens when agents complete tasks

**Example Secure Usage:**
```bash
# Issue token
curl -X POST "/api/v1/ie/issue-atk" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user-123","audience_sp_id":"https://api.service.com","permissions":["read:basic"],"purpose":"User requested summary","model_id":"gpt-4-turbo"}'

# Use the ATK with the target service
curl -X GET "https://api.service.com/data" \
  -H "Authorization: Bearer $AGENT_TOKEN"

# Revoke when done
curl -X POST "/reg/revoke-atk" \
  -H "Authorization: Bearer $API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"jti":"token-jti-from-atk"}'
```

---

## Supported Values

### AI Models

<details>
<summary><strong>OpenAI Models</strong></summary>

```
gpt-4.1
gpt-4.1-mini
gpt-4.1-nano
gpt-4o
gpt-4o-mini
gpt-4-turbo
gpt-3.5-turbo
o3
o3-mini
o1-preview
o1-mini
```

</details>

<details>
<summary><strong>Anthropic Claude Models</strong></summary>

```
claude-sonnet-4-20250514
claude-opus-4
claude-3.7-sonnet
claude-3.5-sonnet-20241022
claude-3.5-haiku-20241022
claude-3-opus-20240229
claude-3-sonnet-20240229
claude-3-haiku-20240307
```

</details>

<details>
<summary><strong>Google Gemini Models</strong></summary>

```
gemini-2.5-pro-experimental
gemini-2.5-flash
gemini-2.0-flash
gemini-2.0-flash-lite
gemini-2.0-pro-experimental
gemini-1.5-pro-latest
gemini-1.5-flash-latest
```

</details>

<details>
<summary><strong>xAI Models</strong></summary>

```
grok-3
grok-2
grok-1.5
```

</details>

<details>
<summary><strong>Meta Llama Models</strong></summary>

**Llama 4 Generation:**
```
llama-4-scout-17b
llama-4-maverick-17b
```

**Llama 3.3 Generation:**
```
llama-3.3-70b
llama-3.3-70b-instruct
```

**Llama 3.2 Generation:**
```
llama-3.2-90b-vision
llama-3.2-11b-vision
llama-3.2-3b
llama-3.2-1b
llama-3.2-3b-instruct
llama-3.2-1b-instruct
```

**Llama 3.1 Generation:**
```
llama-3.1-405b
llama-3.1-405b-instruct
llama-3.1-70b
llama-3.1-70b-instruct
llama-3.1-8b
llama-3.1-8b-instruct
```

**Legacy Llama:**
```
meta-llama/Meta-Llama-3-70B-Instruct
llama-3-70b-instruct
llama-3-8b-instruct
```

</details>

<details>
<summary><strong>Mistral Models</strong></summary>

**Latest Generation:**
```
mistral-large-2
pixtral-large
mistral-medium-3
mistral-small-3.1
```

**Reasoning Models:**
```
magistral-medium
magistral-small-24b
```

**Specialized Models:**
```
mistral-nemo-12b
codestral-22b
codestral-mamba-7b
mathstral-7b
```

**Core Models:**
```
mistral-7b-v0.3
mistral-7b-instruct-v0.3
mixtral-8x7b-instruct-v0.1
mixtral-8x22b-instruct-v0.1
```

**Legacy naming:**
```
mistralai/Mistral-7B-Instruct-v0.2
mistralai/Mixtral-8x7B-Instruct-v0.1
```

</details>

<details>
<summary><strong>Alibaba Qwen Series</strong></summary>

```
qwen-2.5-max
qwen-2.5-72b-instruct
qwen-2.5-32b-instruct
qwen-2.5-14b-instruct
qwen-2.5-7b-instruct
qwen-2.5-3b-instruct
qwen-2.5-1.5b-instruct
qwen-2.5-coder-32b
qwen-2.5-math-72b
qwen-2.5-vl-72b
```

</details>

<details>
<summary><strong>DeepSeek Models</strong></summary>

```
deepseek-r1
deepseek-v3
deepseek-coder-v2-236b
deepseek-coder-33b-instruct
deepseek-math-7b
deepseek-chat
```

</details>

<details>
<summary><strong>Other Chinese Models</strong></summary>

```
yi-34b-chat
yi-6b-chat
baichuan2-13b-chat
chatglm3-6b
internlm2-20b
```

</details>

<details>
<summary><strong>Cohere Models</strong></summary>

```
command-r-plus
command-r
command-light
command-nightly
```

</details>

<details>
<summary><strong>Microsoft Models</strong></summary>

```
phi-3.5-mini-instruct
phi-3.5-moe-instruct
phi-3-medium-instruct
microsoft/phi-2
orca-2-13b
orca-2-7b
```

</details>

<details>
<summary><strong>Open Source Community Models</strong></summary>

**Large Models:**
```
bloom-176b
falcon-180b
falcon-40b
falcon-7b
```

**Popular Community Models:**
```
starling-lm-7b-alpha
openchat-3.5-0106
zephyr-7b-beta
vicuna-13b-v1.5
vicuna-7b-v1.5
wizardlm-70b-v1.0
wizardlm-13b-v1.2
alpaca-7b
```

**Legacy naming:**
```
HuggingFaceH4/zephyr-7b-alpha
openchat/openchat-3.5-0106
```

**Code Specialists:**
```
code-llama-34b-instruct
code-llama-13b-instruct
code-llama-7b-instruct
wizardcoder-34b-v1.0
starcoder2-15b
starcoder2-7b
```

</details>

<details>
<summary><strong>AI21 Models</strong></summary>

```
jurassic-2-ultra
jurassic-2-mid
jurassic-2-light
```

</details>

<details>
<summary><strong>Stability AI Models</strong></summary>

```
stable-code-3b
stablelm-2-12b
stablelm-2-1.6b
```

</details>

<details>
<summary><strong>Multimodal Specialists</strong></summary>

```
llava-1.6-34b
llava-1.6-13b
llava-1.6-7b
blip2-flan-t5-xl
instructblip-7b
minigpt-4
```

</details>

<details>
<summary><strong>Alternative Architectures</strong></summary>

```
rwkv-4-7b
mamba-2.8b
retnet-7b
jamba-instruct
```

</details>

### Standard Permissions

- `read:articles_all` - Read all articles
- `read:user_profile_basic` - Read basic user profile
- `summarize:text_content_short` - Create short summaries
- `analyze:sentiment_text` - Analyze text sentiment
- `interact:chatbot_basic` - Basic chatbot interactions

**Custom permissions are supported** - use descriptive, colon-separated format like `action:resource_scope`
