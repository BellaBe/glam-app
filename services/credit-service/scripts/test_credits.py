#!/usr/bin/env python3
"""
Test script for credit service API endpoints.

Usage:
    python scripts/test_credit.py
"""

import asyncio
import json
import uuid
from decimal import Decimal
from typing import Dict, Any

import httpx


class CreditServiceTester:
    """Test credit service functionality"""
    
    def __init__(self, base_url: str = "http://localhost:8015"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_merchant_id = str(uuid.uuid4())
    
    async def test_health(self) -> Dict[str, Any]:
        """Test health endpoint"""
        print("Testing health endpoint...")
        
        response = await self.client.get(f"{self.base_url}/api/v1/health")
        
        print(f"Health Status: {response.status_code}")
        print(f"Response: {response.json()}")
        
        return response.json()
    
    async def test_plugin_status(self, merchant_id: str) -> Dict[str, Any]:
        """Test plugin status endpoint"""
        print(f"\nTesting plugin status for merchant {merchant_id}...")
        
        response = await self.client.get(
            f"{self.base_url}/api/v1/credits/plugin-status/{merchant_id}"
        )
        
        print(f"Plugin Status: {response.status_code}")
        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)}")
        
        return data
    
    async def test_get_account(self, merchant_id: str) -> Dict[str, Any]:
        """Test get account endpoint"""
        print(f"\nTesting get account for merchant {merchant_id}...")
        
        response = await self.client.get(
            f"{self.base_url}/api/v1/credits/accounts/{merchant_id}"
        )
        
        print(f"Get Account Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"Error: {response.text}")
            return {}
    
    async def test_get_balance(self, merchant_id: str) -> Dict[str, Any]:
        """Test get balance endpoint"""
        print(f"\nTesting get balance for merchant {merchant_id}...")
        
        response = await self.client.get(
            f"{self.base_url}/api/v1/credits/accounts/{merchant_id}/balance"
        )
        
        print(f"Get Balance Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"Error: {response.text}")
            return {}
    
    async def test_get_transactions(self, merchant_id: str) -> Dict[str, Any]:
        """Test get transactions endpoint"""
        print(f"\nTesting get transactions for merchant {merchant_id}...")
        
        response = await self.client.get(
            f"{self.base_url}/api/v1/credits/transactions",
            params={"merchant_id": merchant_id, "page": 1, "limit": 10}
        )
        
        print(f"Get Transactions Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            return data
        else:
            print(f"Error: {response.text}")
            return {}
    
    async def run_all_tests(self):
        """Run all tests"""
        try:
            print("=" * 60)
            print("CREDIT SERVICE API TESTS")
            print("=" * 60)
            
            # Test health
            await self.test_health()
            
            # Test with new merchant (should trigger account creation)
            await self.test_plugin_status(self.test_merchant_id)
            
            # Test account operations
            await self.test_get_account(self.test_merchant_id)
            await self.test_get_balance(self.test_merchant_id)
            await self.test_get_transactions(self.test_merchant_id)
            
            # Test with different merchant
            other_merchant_id = str(uuid.uuid4())
            await self.test_plugin_status(other_merchant_id)
            
            print("\n" + "=" * 60)
            print("ALL TESTS COMPLETED")
            print("=" * 60)
            
        except Exception as e:
            print(f"Test failed with error: {e}")
            raise
        finally:
            await self.client.aclose()


async def main():
    """Main test function"""
    tester = CreditServiceTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())