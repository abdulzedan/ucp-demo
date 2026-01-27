# UCP Demo

An interactive demonstration of the **Universal Commerce Protocol (UCP)** - an open standard enabling interoperability between commerce entities for seamless commerce integrations.

## What is UCP?

The Universal Commerce Protocol addresses the fragmented commerce landscape by providing a standardized common language. It enables:

- **AI Agents** to autonomously discover, browse, and purchase from any UCP-compliant business
- **Businesses** to declare capabilities (Checkout, Order, Payments) in a standardized way
- **Payment Providers** to securely exchange tokens without exposing raw credentials

### Key Features Demonstrated

- **Capability Discovery** - Business profiles at `/.well-known/ucp`
- **Checkout Flow** - Full session lifecycle with extensions
- **Payment Handling** - Secure tokenization without PCI scope
- **AI Shopping Agent** - Conversational commerce with Gemini
- **Protocol Visualization** - Real-time message inspection

## Quick Start

### Prerequisites

- Python 3.11+
- Poetry
- Node.js 18+ (for frontend)
- Google Gemini API key (optional - for AI conversational agent)

### Setup

```bash
# Clone the repository
git clone https://github.com/abdulzedan/ucp-demo.git
cd ucp-demo

# One-command setup
make setup

# Or manually:
poetry install
cd frontend && npm install
```

### Running the Demo

```bash
# Start everything (backend + frontend)
make dev

# Or run separately:
make backend   # Backend only at http://localhost:8000
make frontend  # Frontend only at http://localhost:5173
```

### Configuration (Optional)

```bash
# Copy environment template
cp .env.example .env

# Add your Gemini API key for AI-powered shopping assistant
# GOOGLE_API_KEY=your-key-here
# USE_LLM=true
```

### Available Commands

```bash
make help      # Show all available commands
make dev       # Start development servers
make build     # Build frontend for production
make test      # Run tests
make lint      # Run linters
make clean     # Clean build artifacts
```

## Architecture

```
┌──────────────────┐     ┌──────────────────┐     ┌──────────────┐
│   React Frontend │────▶│  Platform Agent  │────▶│ Mock Business│
│   (Chat + Viz)   │     │   (Python/AI)    │     │   (FastAPI)  │
└──────────────────┘     └──────────────────┘     └──────────────┘
         │                        │                       │
         └────────────────────────┴───────────────────────┘
                         Protocol Visualizer
                    (Real-time UCP message display)
```

## Demo Walkthrough

### 1. Discover the Business

```bash
curl http://localhost:8000/.well-known/ucp
```

Returns the business profile with supported capabilities and payment handlers.

### 2. Browse Products

```bash
curl http://localhost:8000/api/v1/products
```

### 3. Create Checkout Session

```bash
curl -X POST http://localhost:8000/api/v1/checkout-sessions \
  -H "Content-Type: application/json" \
  -d '{
    "line_items": [
      {"product_id": "coffee_large", "quantity": 1}
    ]
  }'
```

### 4. Complete Checkout

```bash
curl -X POST http://localhost:8000/api/v1/checkout-sessions/{id}/complete \
  -H "Content-Type: application/json" \
  -d '{
    "payment": {
      "instruments": [{
        "handler_id": "mock_tokenizer_001",
        "credential": {"type": "TOKEN", "token": "tok_demo_123"}
      }]
    }
  }'
```

## Project Structure

```
ucp-demo/
├── backend/
│   ├── business/      # Mock UCP-compliant merchant
│   ├── platform/      # AI shopping agent
│   ├── visualizer/    # Protocol message streaming
│   └── schemas/       # UCP Pydantic models
├── frontend/          # React chat + visualizer
├── docs/
│   └── UCP_OVERVIEW.md
└── README.md
```

## UCP Resources

- [UCP Specification](https://ucp.dev/specification/overview)
- [Official Samples](https://github.com/Universal-Commerce-Protocol/samples)
- [UCP Schema Reference](https://ucp.dev/schemas/)

## License

Apache 2.0
