# Secure, Verifiable IAM for AI Agents

Heimdall provides a secure, verifiable Identity and Access Management (IAM) framework specifically designed for AI agents, enabling them to operate with proper authentication, authorization, and accountability across digital services.

## Table of Contents

1. [Introduction](#introduction)
2. [The Challenge: Identifying AI Agents](#the-challenge-identifying-ai-agents)
3. [Proposed Solution: A Dedicated Identity Layer](#solution-a-dedicated-identity-layer)
4. [How it Works: Core Components](#how-it-works-core-components)
5. [Key Concepts in Action](#key-concepts-in-action)
6. [Why IAM for AI Agents: Benefits](#benefits)
7. [Use Cases](#use-cases)

---
## Introduction - The Need for Agent Identity

Artificial Intelligence (AI) agents are transitioning from tools to autonomous actors, operating across the digital landscape on behalf of users. This evolution demands a robust way to manage their identity, permissions, and actions. Today's methods—shared credentials, static API keys, or simple User-Agent strings—fall short, creating security risks and lacking the necessary control and accountability.

This Agent Identity Framework (AIF/Heimdall) addresses this gap by establishing a dedicated identity layer for AI agents. Built on proven standards like JWT and public-key cryptography, AIF provides a standardized, secure, and verifiable way for agents to identify themselves, prove their authorization, and interact responsibly with online services.

---
## The Challenge - Identifying AI Agents

- **Authentication**: How does a service (website, API) know it's interacting with a legitimate AI agent versus a human, a simple bot, or a malicious actor? How can it verify the agent is acting with valid user consent?

- **Authorization**: How can users and services grant agents specific, limited permissions instead of broad access via shared credentials or overly permissive API keys?

- **Accountability**: How can actions taken by autonomous agents be reliably attributed back to the specific agent instance, its provider, and the delegating user for security and compliance?

- **Trust & Interoperability**: How can services make informed decisions about interacting with diverse agents from various providers in a standardized way?

Current methods – relying on User-Agent strings (easily spoofed), IP addresses (unreliable), or sharing user credentials/static API keys – are inadequate, insecure, and non-standardized for the complex interactions autonomous agents will undertake.

---
## Solution - A Dedicated Identity Layer

Heimdall is proposed as a standardized, secure, and verifiable identity layer specifically designed for AI agents, treating them as first-class digital entities. It aims to provide the foundational infrastructure for trust and accountability in the agent ecosystem.

**Core Goals:**

- **Verifiable Identity**: Provide a standard way to uniquely identify agent instances and their origins.
- **Secure Delegation**: Enable users to securely grant specific, revocable permissions to agents.
- **Standardized Authorization**: Allow services to reliably verify agent permissions.
- **Transparent Accountability**: Facilitate clear audit trails for agent actions.

---
## How it Works - Core Components

Heimdall integrates proven web standards (URIs, JWT, PKI) with agent-specific concepts:

- **(AID) Agent ID**: A structured URI (`aif://issuer/model/user-or-pseudo/instance`) uniquely identifying each agent instance and its context (who issued it, what model, who delegated). Supports pseudonymity for user privacy.

- **(ATK) Agent Token**: A short-lived, cryptographically signed JSON Web Token (JWT). The ATK acts as the agent's "digital passport," containing:
    - The agent's AID (*sub* claim).
    - The issuing entity (*iss* claim).
    - The intended audience/service (*aud* claim).
    - Explicit, granular permissions granted to the agent (actions + conditions).
    - The purpose of the delegation.
    - Verifiable trust_tags indicating issuer reputation, capabilities, user verification level, etc. This is optional.

- **(REG) Registry Service**: A verification infrastructure (initially centralized/OSS, potentially federated later) where:
    - Services retrieve Issuing Entity public keys to verify ATK signatures.
    - Token revocation status can be checked.
    - Issuer legitimacy can be confirmed.

- **(TRUST) Trust Mechanisms**: A phased approach starting with verifiable attributes (trust_tags in the ATK) allowing services to assess agent trustworthiness based on concrete data, evolving potentially towards dynamic scoring.

- **(SIG) Agent Signature**: Standard asymmetric cryptography (Ed25519/ECDSA) used by Issuing Entities to sign ATKs, ensuring authenticity and integrity.

---
## Key Concepts in Action

**Key Entities in the Ecosystem**

- **User**: The human principal delegating authority to an AI agent.
- **Issuing Entity (IE)**: An organization authorized to issue AIDs and sign ATKs for agents (e.g., AI providers, agent application builders).
- **AI/LLM Provider**: The entity providing the underlying AI model capabilities.
- **Service Provider (SP)**: Digital services, websites, or APIs that agents interact with.
- **Registry Operator**: Entity maintaining instances of the Registry Service (REG).
- **Agent Builder**: Developer or organization creating the agent application/service.

### Sample Workflow

1. **Delegation**: A User authorizes an Agent Platform (Issuing Entity) to act on their behalf for a specific purpose with defined permissions (e.g., via an enhanced OAuth/OIDC flow). This can be extended to multi layer delegation - agent to agent.

2. **Issuance**: The Issuing Entity generates an AID and issues a signed ATK containing the AID, permissions, purpose, and trust tags.

3. **Interaction**: The Agent presents its ATK (e.g., in an HTTP header) when interacting with a Service Provider.

4. **Validation**: The Service Provider:
     1. Retrieves the Issuing Entity's public key from the REG service.
     2. Verifies the ATK's signature and standard claims (expiry, audience).
     3. Checks the token's revocation status via the REG.
     4. Evaluates the permissions claim against the requested action.
     5. Optionally uses trust_tags for risk assessment or policy decisions.

5. **Accountability**: The Service Provider logs the action with the verified AID and claims from the ATK.

![AIF Verification Flow](/static/assets/sequence-diagram.png)

*AIF Verification Sequence Diagram*

---
## Benefits

### For Service Providers:

- **Enhanced Security**: Reliably distinguish legitimate, authorized agents from spoofed/unauthorized ones. Mitigate risks from credential sharing.
- **Granular Control**: Apply specific policies, rate limits, or access rules based on verifiable agent identity and permissions.
- **Improved Auditability**: Create trustworthy logs of agent actions for compliance and security analysis.
- **Reduced Abuse**: Identify and block misbehaving agents or those from untrusted sources.
- **Analytics**: Standardized way to gather analytics on agent traffic.

### For Agent Builders & AI Providers:

- **Build Trust**: Signal legitimacy and security posture to users and services.
- **Enable Access**: Provide a standard way for agents to access services requiring verification.
- **Differentiation**: Stand out based on verifiable attributes and responsible practices.

### For Users:

- **Better Security**: Reduced need to share primary credentials.
- **Greater Control**: Clearer understanding and management of permissions delegated to agents (via agent platforms).
- **Increased Confidence**: Assurance that agents act within defined boundaries.

---
## Use Cases

Here are the key scenarios where Heimdall provides significant value:

<details>
<summary><strong>Verifiable Agent Identification & Authentication</strong></summary>

<p><strong>Scenario</strong>: A Service Provider (SP), like a financial API or a content platform, receives an incoming request. It needs to reliably determine the nature of the requestor. Is it the legitimate human user? Is it Agent Instance #123 delegated by that user? Is it Agent Instance #456 from a different platform acting for the same user? Or is it a malicious bot spoofing an agent's identity? Applying correct permissions, policies, and logging requires knowing who is truly acting.</p>

<p><strong>Solution Principle</strong>: Agents require unique, verifiable digital identities, distinct from their delegating users. These identities must be cryptographically verifiable, allowing SPs to authenticate the specific agent instance making the request and differentiate it from other agents, users, or fraudulent actors.</p>

<p><strong>Benefit</strong>: Enables service providers to reliably distinguish agent traffic, prevent identity spoofing, apply agent-specific policies (like rate limits or access to specialized endpoints), and build foundational trust necessary for more advanced interactions.</p>

<p><strong>Alternatives & Gaps:</strong></p>
<ul>
<li><strong>User-Agent Strings</strong>: Trivially easy to fake; provide no cryptographic verification; offer limited, non-standardized information.
<br><em>Gap: No verifiability, no unique identity.</em></li>
<li><strong>IP Addresses</strong>: Unreliable identifiers (dynamic IPs, NAT, VPNs, shared cloud infrastructure); identifies network location, not the specific agent instance or its delegation context.
<br><em>Gap: No specific identity, unreliable.</em></li>
<li><strong>Shared User Credentials</strong>: Highly insecure; makes the agent indistinguishable from the user; grants excessive permissions; violates terms of service; prevents agent-specific control or audit.
<br><em>Gap: Blurs identity, insecure, excessive privilege.</em></li>
</ul>

</details>

<details>
<summary><strong>Licensing & Compliance Enforcement</strong></summary>

<p><strong>Scenario</strong>: A software company licenses an API or dataset differently for direct human use versus automated use by AI agents. They need a reliable way to enforce these terms. Similarly, regulated industries may require proof that AI accessing sensitive data meets specific compliance standards (tied to the agent model or issuer).</p>

<p><strong>Solution Principle</strong>: Access control policies check the verifiable agent identity. Policies can verify if the associated user/organization has the appropriate "agent access license". Claims within the ATK (aif_trust_tags) could also attest to the agent model's compliance certifications or the issuer's audited status.</p>

<p><strong>Benefit</strong>: Enables more future ready and possibly sophisticated licensing models based on usage type (human vs. agent). Allows enforcement of compliance requirements by verifying agent/issuer attributes against policy before granting access to regulated data or functions.</p>

<p><strong>Alternatives & Gaps:</strong></p>
<ul>
<li><strong>Terms of Service / Honor System</strong>: Relies on users/developers behaving correctly. Ineffective against deliberate misuse.
<br><em>Gap: No enforcement.</em></li>
<li><strong>Heuristic Usage Analysis</strong>: Trying to detect automated usage based on patterns. Can be unreliable, generate false positives/negatives.
<br><em>Gap: Indirect, potentially inaccurate.</em></li>
</ul>

</details>

<details>
<summary><strong>Granular Authorization & Least Privilege</strong></summary>

<p><strong>Scenario</strong>: A user asks an agent to book a specific flight for them. The agent might use the user's main travel account credentials. If these credentials also allow cancelling all trips or changing account details, the agent has far more power than needed for its task, increasing the risk of accidental or malicious misuse.</p>

<p><strong>Solution Principle</strong>: Agents must operate under the principle of least privilege. Authorization mechanisms must allow users (or organizations) to grant agents specific, limited permissions sufficient only for the delegated task and context, separate from the delegator's full entitlements.</p>

<p><strong>Benefit</strong>: Minimizes the potential damage if an agent is compromised or behaves incorrectly. Enables safer automation of sensitive functions by strictly scoping agent capabilities. Allows service providers to enforce fine-grained access control tailored to the agent's specific role.</p>

<p><strong>Alternatives & Gaps:</strong></p>
<ul>
<li><strong>Shared User Credentials</strong>: Agent inherits all user permissions. Fails least privilege entirely.
<br><em>Gap: No granularity.</em></li>
<li><strong>Static API Keys with Broad Permissions</strong>: Often grants wide access (e.g., read/write to a whole data category). Managing numerous keys for very fine-grained access becomes complex.
<br><em>Gap: Often lacks task-specific granularity, management overhead.</em></li>
<li><strong>Standard OAuth Scopes</strong>: While better and closest to the best we have, scopes are often coarse-grained (e.g., email, profile, files.readwrite) and defined by the SP, lacking the context of the specific agent task. They don't easily express complex conditions (e.g., "transaction_limit:$50").
<br><em>Gap: Often lacks fine granularity and conditionality needed for agents.</em></li>
</ul>

</details>

<details>
<summary><strong>Secure & Verifiable Delegation of Authority</strong></summary>

<p><strong>Scenario</strong>: An agent requests access to a user's private medical records via a healthcare API. The API provider needs irrefutable proof that the specific human user explicitly consented to this particular agent accessing this specific data for this specific purpose.</p>

<p><strong>Solution Principle</strong>: There must be a cryptographically verifiable link between an agent's action and the explicit act of delegation by an authenticated principal (user or organization). This link should ideally capture the scope and purpose of the delegation.</p>

<p><strong>Benefit</strong>: Establishes a clear, non-repudiable chain of authority. Protects users by ensuring their consent is explicitly tied to agent actions. Protects SPs by providing proof of authorization before granting access to sensitive resources or actions.</p>

<p><strong>Alternatives & Gaps:</strong></p>
<ul>
<li><strong>Agent Self-Attestation</strong>: The agent merely claims it's authorized. Completely untrustworthy.
<br><em>Gap: No verification.</em></li>
<li><strong>API Key Implies Delegation</strong>: Assumes possession of a key equals authority for any action the key allows. Doesn't prove specific user consent for the agent's task.
<br><em>Gap: No proof of specific user consent.</em></li>
<li><strong>Standard OAuth Authorization Code Flow</strong>: Verifies user consent for the client application (Agent Platform) to access certain scopes. It doesn't inherently create a verifiable link to a specific agent instance or the fine-grained permissions/purpose of the delegation without significant, non-standard extensions.
<br><em>Gap: Focuses on client app authorization, not specific agent instance delegation proof.</em></li>
</ul>

</details>

<details>
<summary><strong>Transparent & Attributable Auditing</strong></summary>

<p><strong>Scenario</strong>: A configuration change is made via API, causing an outage. Investigation reveals the change originated from an IP address associated with an Agent Builder platform. Was it Agent X acting for User A, Agent Y for User B, a rogue employee, or a compromised credential?</p>

<p><strong>Solution Principle</strong>: Interactions involving agents must generate secure, detailed audit logs containing verifiable, unique identifiers that reliably attribute each action to the specific agent instance, its issuing platform/provider, the delegating principal, and ideally the task purpose.</p>

<p><strong>Benefit</strong>: Enables accurate security forensics, incident response, performance analysis, compliance reporting, and dispute resolution by providing a clear, trustworthy record of "who did what, acting for whom, and why".</p>

<p><strong>Alternatives & Gaps:</strong></p>
<ul>
<li><strong>Standard Web/API Logs</strong>: Grossly insufficient for attributing actions to specific agents or delegations.
<br><em>Gap: Lacks verifiable agent/delegation identity.</em></li>
<li><strong>OAuth Client ID Logging</strong>: Identifies the Agent Platform, but not the specific agent instance or user delegation behind the action.
<br><em>Gap: Insufficient granularity.</em></li>
<li><strong>Proprietary Platform Logging</strong>: Each Agent Builder might have internal logs, but the Service Provider needs its own verifiable logs based on the credentials presented to it.
<br><em>Gap: Not standardized, not available/verifiable by SP.</em></li>
</ul>

</details>

<details>
<summary><strong>Standardized Trust & Reputation Signals</strong></summary>

<p><strong>Scenario</strong>: An SP wants to implement risk-based access control. It might trust an agent delegated by a user who authenticated with strong MFA more than one delegated after a simple email verification. It might trust agents issued by established, certified providers more than unknown ones.</p>

<p><strong>Solution Principle</strong>: A standardized mechanism is needed to securely convey verifiable attributes about the agent's context, such as the issuer's reputation tier, the user verification method used during delegation, or declared agent capabilities. This allows SPs to build trust dynamically.</p>

<p><strong>Benefit</strong>: Enables sophisticated risk-based policies, incentivizes responsible practices by Issuing Entities, promotes a healthier ecosystem by allowing differentiation based on verifiable trust signals.</p>

<p><strong>Alternatives & Gaps:</strong></p>
<ul>
<li><strong>IP Reputation/Geo-IP</strong>: Irrelevant for assessing delegation trust or agent capability.
<br><em>Gap: Wrong signals.</em></li>
<li><strong>Manual SP Due Diligence/Allowlisting</strong>: Doesn't scale to a large number of Issuing Entities/Agent Builders. Subjective.
<br><em>Gap: Not scalable, not standardized.</em></li>
<li><strong>Proprietary Risk Scores/Signals</strong>: Leads to fragmentation; lacks transparency and interoperability.
<br><em>Gap: Not standardized, opaque.</em></li>
</ul>

</details>

<details>
<summary><strong>Differentiating Agent Access from Abuse</strong></summary>

<p><strong>Scenario</strong>: A popular e-commerce site or event ticketing platform is plagued by sophisticated bots scraping pricing data excessively or attempting to hoard limited inventory faster than human users can react. Blocking based on IP or simple CAPTCHAs is often ineffective.</p>

<p><strong>Solution Principle</strong>: Implement policies that differentiate access based on verifiable agent identity. Legitimate agents present verifiable credentials. Unverifiable or anonymous automated traffic can be strictly rate-limited or blocked.</p>

<p><strong>Benefit</strong>: Allows SPs to welcome beneficial automation while effectively mitigating abusive automation. Protects platform integrity and ensures fairer access for human users.</p>

<p><strong>Alternatives & Gaps:</strong></p>
<ul>
<li><strong>Advanced Bot Detection</strong>: Can be effective but often results in an arms race; may block legitimate automation or inconvenience humans.
<br><em>Gap: Focuses on blocking bad behavior, not enabling good automation.</em></li>
<li><strong>Strict Rate Limiting</strong>: Can throttle legitimate use cases along with abuse.
<br><em>Gap: Indiscriminate.</em></li>
<li><strong>Proof-of-Work/CAPTCHA</strong>: Adds friction, potentially solvable by sophisticated bots.
<br><em>Gap: Friction, potentially ineffective.</em></li>
</ul>

</details>

<details>
<summary><strong>Physical Devices & IoT Interactions</strong></summary>

<p><strong>Scenario</strong>: A user wants their AI assistant agent to control smart home devices (lights, thermostat, locks) via the device manufacturer's cloud API. The API needs assurance that the command originates from an entity genuinely authorized by the homeowner.</p>

<p><strong>Solution Principle</strong>: The agent authenticates to the IoT platform's API using a verifiable identity token that proves it was delegated by the registered homeowner with specific permissions (e.g., <code>{"action": "set_thermostat", "device_id": "thermo123", "conditions": {"min_temp": 18, "max_temp": 25}}</code>).</p>

<p><strong>Benefit</strong>: Enables secure, delegated control of physical systems via AI agents, preventing unauthorized access or manipulation while providing an audit trail tied to the specific agent and user delegation.</p>

<p><strong>Alternatives & Gaps:</strong></p>
<ul>
<li><strong>Shared API Keys per User</strong>: If the key leaks from one agent/app, all devices are compromised. Lacks granularity.
<br><em>Gap: Security risk, no granular control.</em></li>
<li><strong>Standard OAuth per Device/Platform</strong>: Better, but the SP still only sees the "Agent Platform" client ID, not the specific agent instance or task purpose.
<br><em>Gap: Lacks agent-specific identity and context.</em></li>
</ul>

</details>

<details>
<summary><strong>Verifiable Identity in Agent-Initiated Communication</strong></summary>

<p><strong>Scenario</strong>: An agent initiates a phone call or sends an email/chat message on behalf of a user (e.g., appointment scheduling, customer service inquiry). The recipient needs to know if the communication is genuinely from an authorized agent representing that user or if it's spam/phishing.</p>

<p><strong>Solution Principle</strong>: The communication protocol incorporates or references a verifiable agent credential. For calls, this could be integrated via STIR/SHAKEN extensions or call setup protocols. For email/chat, headers or embedded tokens could carry the verifiable assertion.</p>

<p><strong>Benefit</strong>: Allows recipients to verify the legitimacy of agent-initiated communications, filter spam/impersonation attempts, prioritize trusted interactions, and access relevant context about the agent's purpose.</p>

<p><strong>Alternatives & Gaps:</strong></p>
<ul>
<li><strong>No Verification</strong>: Recipient relies on heuristics, caller ID number (spoofable), email headers (spoofable), or content analysis. Prone to spam and phishing.
<br><em>Gap: No reliable verification.</em></li>
<li><strong>Proprietary Platform Markers</strong>: E.g., Google Duplex identifying itself verbally. Not standardized, not cryptographically verifiable, limited to specific platforms.
<br><em>Gap: Not standard, not verifiable.</em></li>
</ul>

</details>

<details>
<summary><strong>Secure Agent Lifecycle Management</strong></summary>

<p><strong>Scenario</strong>: An agent instance is long-running, but the user's circumstances change (e.g., they leave the company that delegated the agent, or they explicitly revoke permission for a specific task). How can access be reliably terminated? How can agent software be securely updated?</p>

<p><strong>Solution Principle</strong>: While tokens are short-lived, the underlying agent identity and its association with the delegating user/principal need lifecycle management. A robust verifiable revocation mechanism is the key.</p>

<p><strong>Benefit</strong>: Provides mechanisms beyond token expiry for managing agent authorization over time, responding to changes in user status or explicit revocation requests, and potentially tracking agent software versions via metadata linked to the agent identity.</p>

<p><strong>Alternatives & Gaps:</strong></p>
<ul>
<li><strong>Relying Solely on Token Expiry</strong>: Doesn't handle immediate revocation needs.
<br><em>Gap: Lacks immediate revocation.</em></li>
<li><strong>Proprietary Agent Management Platforms</strong>: Each builder creates their own lifecycle system.
<br><em>Gap: Not standardized, no interoperable revocation signal to SPs.</em></li>
<li><strong>OAuth Refresh Token Revocation</strong>: Revokes the platform's ability to get new tokens, but doesn't target specific agent instances or delegations granularly.
<br><em>Gap: Coarse-grained revocation.</em></li>
</ul>

</details>

---

**Reference**: This framework is informed in part by ["Authenticated Delegation and Authorized AI Agents" (South et al., 2024)](https://arxiv.org/pdf/2501.09674), which introduced a structured approach to delegating authority from users to AI systems through extensions to OAuth 2.0 and OpenID Connect.