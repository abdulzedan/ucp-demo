"""Core UCP schema types based on the official UCP specification."""

from datetime import date
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class UCPVersion(str):
    """UCP version in YYYY-MM-DD format."""

    @classmethod
    def current(cls) -> str:
        return "2026-01-11"


class TransportType(str, Enum):
    """Supported transport protocols."""

    REST = "rest"
    MCP = "mcp"
    A2A = "a2a"
    EMBEDDED = "embedded"


class UCPService(BaseModel):
    """Service definition for UCP profile."""

    version: str = Field(
        default="2026-01-11",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Service version in YYYY-MM-DD format",
    )
    spec: str = Field(description="URL to service documentation")
    transport: TransportType = Field(description="Transport protocol")
    endpoint: str | None = Field(
        default=None, description="Business's endpoint for this transport"
    )
    schema_url: str | None = Field(
        default=None,
        alias="schema",
        description="URL to OpenAPI/OpenRPC spec",
    )

    model_config = {"populate_by_name": True}


class UCPCapability(BaseModel):
    """Capability definition for UCP profile."""

    version: str = Field(
        default="2026-01-11",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Capability version in YYYY-MM-DD format",
    )
    spec: str = Field(description="URL to capability specification")
    schema_url: str = Field(
        alias="schema", description="URL to JSON Schema for this capability"
    )
    extends: str | None = Field(
        default=None,
        description="Parent capability this extends (for extensions)",
    )
    config: dict[str, Any] | None = Field(
        default=None, description="Capability-specific configuration"
    )

    model_config = {"populate_by_name": True}


class UCPPaymentHandler(BaseModel):
    """Payment handler definition for UCP profile."""

    id: str = Field(description="Unique identifier for this handler instance")
    version: str = Field(
        default="2026-01-11",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="Handler version",
    )
    spec: str | None = Field(
        default=None, description="URL to handler specification"
    )
    schema_url: str | None = Field(
        default=None, alias="schema", description="URL to handler schema"
    )
    config: dict[str, Any] | None = Field(
        default=None, description="Handler-specific configuration"
    )

    model_config = {"populate_by_name": True}


class SigningKey(BaseModel):
    """JWK signing key for authentication."""

    kid: str = Field(description="Key ID")
    kty: str = Field(description="Key type (e.g., EC)")
    crv: str | None = Field(default=None, description="Curve (for EC keys)")
    x: str | None = Field(default=None, description="X coordinate (for EC keys)")
    y: str | None = Field(default=None, description="Y coordinate (for EC keys)")
    use: str = Field(default="sig", description="Key usage")
    alg: str = Field(default="ES256", description="Algorithm")


class UCPMetadata(BaseModel):
    """UCP metadata block for profiles and responses."""

    version: str = Field(
        default="2026-01-11",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="UCP version",
    )
    services: dict[str, list[UCPService]] = Field(
        default_factory=dict,
        description="Service registry keyed by reverse-domain name",
    )
    capabilities: dict[str, list[UCPCapability]] = Field(
        default_factory=dict,
        description="Capability registry keyed by reverse-domain name",
    )
    payment_handlers: dict[str, list[UCPPaymentHandler]] = Field(
        default_factory=dict,
        description="Payment handler registry keyed by reverse-domain name",
    )


class UCPProfile(BaseModel):
    """Full UCP profile published by businesses and platforms."""

    ucp: UCPMetadata = Field(description="UCP metadata block")
    signing_keys: list[SigningKey] | None = Field(
        default=None, description="Public keys for signature verification"
    )


class UCPResponseMetadata(BaseModel):
    """UCP metadata included in API responses."""

    version: str = Field(
        default="2026-01-11",
        pattern=r"^\d{4}-\d{2}-\d{2}$",
        description="UCP version used to process request",
    )
    capabilities: dict[str, list[dict[str, str]]] = Field(
        default_factory=dict,
        description="Active capabilities for this response",
    )
    payment_handlers: dict[str, list[dict[str, str]]] = Field(
        default_factory=dict,
        description="Active payment handlers for this response",
    )
