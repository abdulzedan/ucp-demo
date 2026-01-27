# Universal Commerce Protocol (UCP) - Comprehensive Overview

## What is UCP?

The **Universal Commerce Protocol (UCP)** is an open standard that addresses the fragmented commerce landscape by providing a standardized common language and functional primitives. It enables platforms (like AI agents and apps), businesses, Payment Service Providers (PSPs), and Credential Providers (CPs) to communicate effectively, ensuring secure and consistent commerce experiences across the web.

**Version:** `2026-01-11`
**License:** Apache 2.0
**Official Site:** https://ucp.dev

---

## Core Concepts

### 1. The Three Participants

| Participant | Role | Example |
|-------------|------|---------|
| **Platform** | Consumer-facing surface acting on behalf of users | AI agents, shopping apps, websites |
| **Business** | Entity selling goods/services (Merchant of Record) | Online retailers, coffee shops |
| **Payment Credential Provider** | Manages payment credentials securely | Google Pay, Shop Pay, PSPs |

### 2. Discovery Architecture

UCP uses a **server-selects** architecture where businesses publish their capabilities at a well-known URL:

```
GET https://business.example.com/.well-known/ucp
```

This returns a **Business Profile** containing:
- Supported services and transports
- Available capabilities (Checkout, Order, etc.)
- Payment handlers (tokenization methods)
- Signing keys for authentication

### 3. Namespace Governance

All capability names use **reverse-domain naming** to encode governance authority:

```
{reverse-domain}.{service}.{capability}
```

**Examples:**
| Name | Authority | Service | Capability |
|------|-----------|---------|------------|
| `dev.ucp.shopping.checkout` | ucp.dev | shopping | checkout |
| `dev.ucp.shopping.fulfillment` | ucp.dev | shopping | fulfillment |
| `com.google.pay` | google.com | - | payment handler |

---

## Transport Protocols

UCP is **transport-agnostic** and supports multiple protocols:

| Transport | Description | Use Case |
|-----------|-------------|----------|
| **REST** | Standard HTTP/JSON APIs | Primary transport, web apps |
| **MCP** | Model Context Protocol | AI/LLM integrations |
| **A2A** | Agent-to-Agent Protocol | Autonomous AI agents |
| **Embedded** | JSON-RPC for iframes | Embedded checkout widgets |

---

## Capabilities

Capabilities are modular features that businesses can implement:

### Core Capabilities

#### 1. Checkout (`dev.ucp.shopping.checkout`)
Facilitates checkout sessions including cart management and tax calculation.

**Operations:**
| Operation | Method | Path | Description |
|-----------|--------|------|-------------|
| Create Checkout | POST | `/checkout-sessions` | Start new session |
| Get Checkout | GET | `/checkout-sessions/{id}` | Retrieve session state |
| Update Checkout | PUT | `/checkout-sessions/{id}` | Update session (full replace) |
| Complete Checkout | POST | `/checkout-sessions/{id}/complete` | Finalize and place order |
| Cancel Checkout | POST | `/checkout-sessions/{id}/cancel` | Cancel session |

**Checkout Status Lifecycle:**
```
incomplete ←→ requires_escalation
     ↓              ↓
ready_for_complete  │
     ↓              │
complete_in_progress
     ↓              ↓
   completed ←──────┘

   canceled (can occur from any state)
```

#### 2. Identity Linking (`dev.ucp.common.identity_linking`)
Enables platforms to obtain OAuth 2.0 authorization to perform actions on a user's behalf.

#### 3. Order (`dev.ucp.shopping.order`)
Webhook-based updates for order lifecycle events (shipped, delivered, returned).

### Extension Capabilities

Extensions augment core capabilities using the `extends` field:

#### Fulfillment (`dev.ucp.shopping.fulfillment`)
- Extends: `dev.ucp.shopping.checkout`
- Adds shipping options and delivery address handling

#### Discount (`dev.ucp.shopping.discount`)
- Extends: `dev.ucp.shopping.checkout`
- Adds promo code and discount functionality

---

## Payment Architecture

### The Trust Triangle

```
           Business
              ↑
    Legal     │     Legal
    Contract  │     Contract
              │
    ┌─────────┴─────────┐
    ↓                   ↓
Platform ◄──────► Payment Provider
           Token/Credential
           Exchange
```

### Payment Flow

1. **Negotiation**: Business advertises payment handlers in UCP profile
2. **Acquisition**: Platform obtains token from payment provider (never raw credentials)
3. **Completion**: Platform submits opaque token to business

### Payment Handlers

Payment handlers are **specifications** (not entities) defining how payment instruments are processed:

```json
{
  "payment_handlers": {
    "com.google.pay": [{
      "id": "gpay_1234",
      "version": "2026-01-11",
      "config": {
        "merchant_id": "01234567890123456789",
        "allowed_payment_methods": [...]
      }
    }]
  }
}
```

### Security Principles

1. **Unidirectional Flow**: Credentials flow Platform → Business only
2. **Opaque Credentials**: Platforms handle tokens, not raw PANs
3. **Handler ID Routing**: Ensures correct decryption keys are used
4. **PCI Scope Minimization**: Platforms avoid PCI-DSS scope by using tokenization

---

## Profile Structures

### Business Profile (`/.well-known/ucp`)

```json
{
  "ucp": {
    "version": "2026-01-11",
    "services": {
      "dev.ucp.shopping": [{
        "version": "2026-01-11",
        "transport": "rest",
        "endpoint": "https://business.example.com/api/v1",
        "schema": "https://ucp.dev/services/shopping/rest.openapi.json"
      }]
    },
    "capabilities": {
      "dev.ucp.shopping.checkout": [{
        "version": "2026-01-11",
        "spec": "https://ucp.dev/specification/checkout",
        "schema": "https://ucp.dev/schemas/shopping/checkout.json"
      }],
      "dev.ucp.shopping.fulfillment": [{
        "version": "2026-01-11",
        "extends": "dev.ucp.shopping.checkout"
      }]
    },
    "payment_handlers": {
      "dev.ucp.demo.tokenizer": [{
        "id": "tokenizer_001",
        "version": "2026-01-11"
      }]
    }
  },
  "signing_keys": [...]
}
```

### Platform Profile (advertised via UCP-Agent header)

```json
{
  "ucp": {
    "version": "2026-01-11",
    "capabilities": {...},
    "payment_handlers": {...}
  },
  "signing_keys": [...]
}
```

---

## Capability Negotiation

### Platform → Business Communication

**REST Transport:**
```http
POST /checkout-sessions HTTP/1.1
UCP-Agent: profile="https://platform.example/ucp-profile.json"
Content-Type: application/json
```

**MCP Transport:**
```json
{
  "jsonrpc": "2.0",
  "method": "create_checkout",
  "params": {
    "meta": {
      "ucp-agent": {
        "profile": "https://platform.example/ucp-profile.json"
      }
    }
  }
}
```

### Intersection Algorithm

1. For each business capability, include if platform has matching `name`
2. Remove extensions where parent capability is not in intersection
3. Repeat until no more capabilities are removed

---

## Checkout Data Structures

### Line Item

```json
{
  "id": "li_001",
  "product_id": "prod_coffee_large",
  "title": "Large Coffee",
  "quantity": 2,
  "unit_price": 499,
  "total_price": 998,
  "currency": "USD"
}
```

### Totals

```json
{
  "subtotal": 1998,
  "discount": 200,
  "shipping": 500,
  "tax": 180,
  "total": 2478,
  "currency": "USD"
}
```

### Messages (Errors/Warnings)

```json
{
  "type": "error",
  "code": "invalid_address",
  "content": "Shipping address is incomplete",
  "severity": "recoverable"
}
```

**Severity Levels:**
| Severity | Meaning | Platform Action |
|----------|---------|-----------------|
| `recoverable` | Platform can fix via API | Call Update Checkout |
| `requires_buyer_input` | Need info not available via API | Handoff via `continue_url` |
| `requires_buyer_review` | Buyer authorization required | Handoff via `continue_url` |

---

## Response Structure

All UCP responses include the `ucp` metadata block:

```json
{
  "ucp": {
    "version": "2026-01-11",
    "capabilities": {
      "dev.ucp.shopping.checkout": [{"version": "2026-01-11"}],
      "dev.ucp.shopping.fulfillment": [{"version": "2026-01-11"}]
    },
    "payment_handlers": {
      "dev.ucp.demo.tokenizer": [{"id": "tokenizer_001", "version": "2026-01-11"}]
    }
  },
  "id": "checkout_abc123",
  "status": "incomplete",
  "line_items": [...],
  ...
}
```

---

## Versioning

UCP uses **date-based versioning** in `YYYY-MM-DD` format.

### Backwards Compatibility Rules

**Allowed without new version:**
- Adding new non-required fields
- Adding new endpoints
- Adding new enum values

**Requires new version:**
- Removing/renaming fields
- Changing field types
- Making non-required fields required

---

## Key Design Principles

1. **Transport Agnostic**: Same protocol works over REST, MCP, or A2A
2. **Composable**: Capabilities and extensions can be mixed and matched
3. **Decoupled Payments**: Platforms never touch raw payment credentials
4. **Agent-First**: Designed for AI agents to autonomously complete commerce
5. **Standards-Based**: Builds on OAuth 2.0, JWK, OpenAPI, JSON Schema

---

## Glossary

| Term | Definition |
|------|------------|
| **Capability** | A standalone feature a business supports (Checkout, Order) |
| **Extension** | Optional module that augments a capability |
| **Payment Handler** | Specification for processing payment instruments |
| **Platform** | Consumer-facing surface (AI agent, app, website) |
| **Business** | Entity selling goods/services (Merchant of Record) |
| **PSP** | Payment Service Provider |
| **AP2** | Agent Payments Protocol for autonomous transactions |
| **MCP** | Model Context Protocol for AI integrations |
| **A2A** | Agent-to-Agent Protocol |
| **VDC** | Verifiable Digital Credential |

---

## Official Resources

- **Specification**: https://ucp.dev/specification/overview
- **Schemas**: https://ucp.dev/schemas/
- **Samples**: https://github.com/Universal-Commerce-Protocol/samples
- **Conformance Tests**: https://github.com/Universal-Commerce-Protocol/conformance
