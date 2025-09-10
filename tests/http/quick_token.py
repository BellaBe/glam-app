#!/usr/bin/env python3
"""
Quick JWT token generator for notification service testing.
Matches the actual client JWT signing pattern.
"""

import os
import sys
import time

import jwt


def sign_jwt(shop):
    """
    Generate a JWT token matching your client's signJwt function.

    Matches the pattern:
    - sub: shop domain
    - scope: "bff:api:access"
    - iat: current timestamp
    - platform: "shopify"
    """

    # Build the payload
    payload = {"sub": shop, "scope": "bff:api:access", "iat": int(time.time()), "platform": "shopify"}

    # Get configuration from environment
    secret = "DLNN6MDM_4X5ez7VY9IdJ7cpl-v20uID4Ff2E9rvR6xb_faOS2GwX6dCehof30CL"
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    expire_seconds = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_SECONDS", "3600"))

    # Add expiration to payload
    payload["exp"] = int(time.time()) + expire_seconds

    # Sign the token
    try:
        token = jwt.encode(payload, secret, algorithm=algorithm)
        return token
    except Exception as e:
        raise Exception(f"Failed to create client JWT: {e}") from e


def main():
    """Generate tokens for testing."""

    # Default test shop or get from command line
    shop = sys.argv[1] if len(sys.argv) > 1 else "test-shop_2.myshopify.com"

    print("=" * 60)
    print("JWT Token Generator for Notification Service")
    print("=" * 60)

    # Show configuration
    print("\nConfiguration:")
    print(f"  Shop Domain: {shop}")
    print("  Scope: bff:api:access")
    print("  Platform: shopify")
    print(f"  Algorithm: {os.getenv('JWT_ALGORITHM', 'HS256')}")
    print(f"  Expires In: {os.getenv('JWT_ACCESS_TOKEN_EXPIRE_SECONDS', '3600')} seconds")

    # Check if secret is configured
    if not os.getenv("CLIENT_JWT_SECRET"):
        print("\n⚠️  WARNING: Using default secret 'your-test-secret'")
        print("   Set CLIENT_JWT_SECRET environment variable for production")

    # Generate token
    try:
        token = sign_jwt(shop)

        print("\n✅ Token generated successfully!")
        print("\nToken:")
        print("-" * 60)
        print(token)
        print("-" * 60)

        print("\nTo use in your .http file, replace this line:")
        print(f"@auth_token = {token}")

        print("\nOr export as environment variable:")
        print(f"export TEST_JWT_TOKEN='{token}'")

        # Decode to show contents (for debugging)
        print("\nToken payload:")
        decoded = jwt.decode(token, options={"verify_signature": False})
        for key, value in decoded.items():
            print(f"  {key}: {value}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
