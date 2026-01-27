"""Discovery schemas for UCP profiles."""

from pydantic import BaseModel, Field

from backend.schemas.ucp import (
    SigningKey,
    UCPCapability,
    UCPMetadata,
    UCPPaymentHandler,
    UCPProfile,
    UCPService,
)


class BusinessProfile(UCPProfile):
    """Business profile published at /.well-known/ucp.

    This profile declares the business's supported services, capabilities,
    and payment handlers for platform discovery.
    """

    pass


class PlatformProfile(UCPProfile):
    """Platform profile hosted at a URI advertised in requests.

    Platforms advertise their profile via the UCP-Agent header (REST)
    or meta object (MCP) to enable capability negotiation.
    """

    pass


def create_demo_business_profile(
    business_url: str,
    business_name: str = "Cymbal Coffee Shop",
) -> BusinessProfile:
    """Create a demo business profile for the mock merchant.

    Args:
        business_url: Base URL of the business server
        business_name: Display name of the business

    Returns:
        BusinessProfile configured for the demo
    """
    return BusinessProfile(
        ucp=UCPMetadata(
            version="2026-01-11",
            services={
                "dev.ucp.shopping": [
                    UCPService(
                        version="2026-01-11",
                        spec="https://ucp.dev/specification/overview",
                        transport="rest",
                        endpoint=f"{business_url}/api/v1",
                        schema_url="https://ucp.dev/services/shopping/rest.openapi.json",
                    )
                ]
            },
            capabilities={
                "dev.ucp.shopping.checkout": [
                    UCPCapability(
                        version="2026-01-11",
                        spec="https://ucp.dev/specification/checkout",
                        schema_url="https://ucp.dev/schemas/shopping/checkout.json",
                    )
                ],
                "dev.ucp.shopping.fulfillment": [
                    UCPCapability(
                        version="2026-01-11",
                        spec="https://ucp.dev/specification/fulfillment",
                        schema_url="https://ucp.dev/schemas/shopping/fulfillment.json",
                        extends="dev.ucp.shopping.checkout",
                    )
                ],
                "dev.ucp.shopping.discount": [
                    UCPCapability(
                        version="2026-01-11",
                        spec="https://ucp.dev/specification/discount",
                        schema_url="https://ucp.dev/schemas/shopping/discount.json",
                        extends="dev.ucp.shopping.checkout",
                    )
                ],
            },
            payment_handlers={
                "dev.ucp.demo.mock_tokenizer": [
                    UCPPaymentHandler(
                        id="mock_tokenizer_001",
                        version="2026-01-11",
                        spec="https://ucp.dev/specification/tokenization-guide",
                        config={
                            "type": "CARD",
                            "supported_networks": ["visa", "mastercard", "amex"],
                            "tokenization_url": f"{business_url}/api/v1/tokenize",
                        },
                    )
                ]
            },
        ),
        signing_keys=[
            SigningKey(
                kid="demo_2026",
                kty="EC",
                crv="P-256",
                x="WbbXwVYGdJoP4Xm3qCkGvBRcRvKtEfXDbWvPzpPS8LA",
                y="sP4jHHxYqC89HBo8TjrtVOAGHfJDflYxw7MFMxuFMPY",
                use="sig",
                alg="ES256",
            )
        ],
    )
