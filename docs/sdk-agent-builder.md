The official Python SDK for Agent Builders to interact with the Agent Identity Framework (AIF) Core Service. Issue and manage Agent Tokens (ATKs) to enable your AI agents to authenticate securely with service providers.

## Installation

```bash
pip install heimdall-agent-builder-sdk
```

## Quick Install & Import Reference

| Action | Command |
|--------|---------|
| **Install** | `pip install heimdall-agent-builder-sdk` |
| **Import** | `from aif_agent_builder_sdk import AIFClient` |
| **Environment** | `AIF_SDK_CORE_URL`, `AIF_SDK_ISSUER_API_KEY` |

> 💡 **Note**: Package name uses "heimdall" but imports use "aif" to maintain consistency with the Agent Identity Framework (AIF) API.

## Quick Start

### Environment Setup

Create a `.env` file or set environment variables:

```bash
AIF_SDK_CORE_URL=http://localhost:5000
AIF_SDK_ISSUER_API_KEY=your-agent-builder-api-key
```

### Basic Usage

```python
import asyncio
from aif_agent_builder_sdk import AIFClient

async def main():
    # Initialize client
    client = AIFClient()
    
    # Request an Agent Token
    token = await client.request_aif_token(
        user_id="user-123",
        audience_sp_id="https://api.example.com",
        permissions=["read:articles_all", "summarize:text_content_short"],
        purpose="Summarize news articles",
        model_id="gpt-4-turbo"
    )
    
    print(f"Token issued: {token.atk[:50]}...")
    
    # Use the token in API requests
    headers = AIFClient.get_aif_authorization_header(token)
    
    # Check if token is revoked
    claims = await client.validate_token_locally(token.atk)
    is_revoked = await client.check_token_revocation_status(claims['jti'])
    print(f"Token revoked: {is_revoked}")
    
    # Revoke the token when done
    await client.revoke_aif_token(claims['jti'])
    
    # Clean up
    await client.close()

asyncio.run(main())
```

### Using Context Manager

```python
from aif_agent_builder_sdk import AIFClient

async with AIFClient() as client:
    token = await client.request_aif_token(
        user_id="user-456",
        audience_sp_id="https://api.example.com",
        permissions=["read:user_profile_basic"],
        purpose="Display user profile",
        model_id="gpt-3.5-turbo"
    )
    # Client automatically closes when exiting context
```

## Features

- **Token Management**: Issue and revoke Agent Tokens (ATKs)
- **Token Verification**: Verify tokens using JWKS with Ed25519 signatures
- **Revocation Checking**: Check token revocation status
- **Async/Await**: Modern asynchronous Python with httpx
- **Type Hints**: Full type annotations for better IDE support
- **Pydantic Models**: Automatic validation of requests and responses

## Configuration

### Client Options

```python
from aif_agent_builder_sdk import AIFClient

client = AIFClient(
    core_service_url="https://aif.example.com",
    issuer_api_key="your-api-key",
    timeout_seconds=30
)
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `AIF_SDK_CORE_URL` | Base URL of the AIF Core Service |
| `AIF_SDK_ISSUER_API_KEY` | Your Agent Builder API key |

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

## Error Handling

```python
from aif_agent_builder_sdk import AIFServiceError, AIFSDKClientError

try:
    token = await client.request_aif_token(...)
except AIFServiceError as e:
    print(f"Service error: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Detail: {e.detail}")
except AIFSDKClientError as e:
    print(f"Client error: {e}")
```

## Full Documentation & Examples

For complete documentation, advanced configuration, integration examples, and troubleshooting:

**[View Full Documentation on GitHub](https://github.com/IAM-Heimdall/heimdall_agent_builder_sdk_python)**

## License

[MIT License](https://github.com/IAM-Heimdall/heimdall_agent_builder_sdk_python/blob/main/LICENSE)