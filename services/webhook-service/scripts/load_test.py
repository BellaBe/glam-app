# services/webhook-service/scripts/load_test.py
#!/usr/bin/env python3
"""
Load test script for webhook service.

This script simulates high-volume webhook traffic to test
the service's performance and reliability.
"""

import asyncio
import aiohttp
import json
import hmac
import hashlib
import base64
import time
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import random


@dataclass
class LoadTestConfig:
    """Configuration for load testing."""
    
    webhook_service_url: str = "http://localhost:8012"
    shopify_secret: str = "test_secret_key"
    concurrent_requests: int = 50
    total_requests: int = 1000
    request_delay_ms: int = 10
    timeout_seconds: int = 30


@dataclass
class LoadTestResult:
    """Result of load testing."""
    
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    requests_per_second: float
    error_distribution: Dict[str, int]


class WebhookLoadTester:
    """Load tester for webhook service."""
    
    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.results: List[Dict[str, Any]] = []
        self.start_time = None
        self.end_time = None
    
    def create_shopify_signature(self, body: str) -> str:
        """Create Shopify HMAC signature."""
        calculated = hmac.new(
            self.config.shopify_secret.encode('utf-8'),
            body.encode('utf-8'),
            hashlib.sha256
        ).digest()
        return base64.b64encode(calculated).decode()
    
    def generate_webhook_payload(self, webhook_type: str, index: int) -> Dict[str, Any]:
        """Generate webhook payload for different types."""
        
        base_time = datetime.utcnow().isoformat() + "Z"
        
        if webhook_type == "orders/create":
            return {
                "id": 1000000 + index,
                "order_number": f"#{1000 + index}",
                "total_price": f"{random.uniform(10, 500):.2f}",
                "currency": "USD",
                "created_at": base_time,
                "updated_at": base_time,
                "line_items": [
                    {
                        "id": 2000000 + index,
                        "product_id": 3000000 + (index % 100),
                        "quantity": random.randint(1, 5),
                        "price": f"{random.uniform(10, 100):.2f}"
                    }
                ],
                "customer": {
                    "id": 4000000 + (index % 1000),
                    "email": f"customer{index}@example.com"
                },
                "shop": {
                    "domain": f"loadtest-shop-{index % 10}.myshopify.com",
                    "id": 5000000 + (index % 10)
                }
            }
        
        elif webhook_type == "products/create":
            return {
                "id": 6000000 + index,
                "title": f"Load Test Product {index}",
                "handle": f"load-test-product-{index}",
                "product_type": "Test Product",
                "vendor": "Load Test Vendor",
                "created_at": base_time,
                "updated_at": base_time,
                "shop": {
                    "domain": f"loadtest-shop-{index % 10}.myshopify.com",
                    "id": 5000000 + (index % 10)
                }
            }
        
        elif webhook_type == "inventory_levels/update":
            return {
                "inventory_item_id": 7000000 + index,
                "location_id": 8000000 + (index % 5),
                "available": random.randint(0, 100),
                "updated_at": base_time,
                "shop": {
                    "domain": f"loadtest-shop-{index % 10}.myshopify.com",
                    "id": 5000000 + (index % 10)
                }
            }
        
        else:
            return {
                "id": 9000000 + index,
                "created_at": base_time,
                "updated_at": base_time,
                "shop": {
                    "domain": f"loadtest-shop-{index % 10}.myshopify.com",
                    "id": 5000000 + (index % 10)
                }
            }
    
    async def send_webhook_request(
        self,
        session: aiohttp.ClientSession,
        webhook_type: str,
        index: int
    ) -> Dict[str, Any]:
        """Send a single webhook request."""
        
        # Generate payload
        payload = self.generate_webhook_payload(webhook_type, index)
        body = json.dumps(payload)
        signature = self.create_shopify_signature(body)
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "X-Shopify-Topic": webhook_type,
            "X-Shopify-Hmac-Sha256": signature,
            "X-Shopify-Shop-Domain": payload["shop"]["domain"],
            "X-Shopify-API-Version": "2024-01",
            "X-Shopify-Webhook-Id": f"load-test-{index}-{int(time.time())}"
        }
        
        # Send request
        url = f"{self.config.webhook_service_url}/webhooks/shopify/{webhook_type.replace('/', '%2F')}"
        
        start_time = time.time()
        result = {
            "index": index,
            "webhook_type": webhook_type,
            "start_time": start_time,
            "success": False,
            "status_code": None,
            "response_time": None,
            "error": None
        }
        
        try:
            async with session.post(url, headers=headers, data=body) as response:
                end_time = time.time()
                result["response_time"] = end_time - start_time
                result["status_code"] = response.status
                result["success"] = response.status == 200
                
                if response.status != 200:
                    result["error"] = f"HTTP {response.status}"
                    response_text = await response.text()
                    result["error_details"] = response_text[:200]
                
        except asyncio.TimeoutError:
            result["error"] = "timeout"
            result["response_time"] = time.time() - start_time
        except Exception as e:
            result["error"] = str(e)
            result["response_time"] = time.time() - start_time
        
        return result
    
    async def run_load_test(self) -> LoadTestResult:
        """Run the load test."""
        
        print(f"🚀 Starting load test with {self.config.total_requests} requests")
        print(f"📊 Concurrency: {self.config.concurrent_requests}")
        print(f"🎯 Target: {self.config.webhook_service_url}")
        print()
        
        # Webhook types to test
        webhook_types = [
            "orders/create",
            "products/create", 
            "inventory_levels/update",
            "orders/updated"
        ]
        
        self.start_time = time.time()
        
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.config.concurrent_requests)
        
        async def bounded_request(session, webhook_type, index):
            async with semaphore:
                if self.config.request_delay_ms > 0:
                    await asyncio.sleep(self.config.request_delay_ms / 1000)
                return await self.send_webhook_request(session, webhook_type, index)
        
        # Create HTTP session with timeout
        timeout = aiohttp.ClientTimeout(total=self.config.timeout_seconds)
        connector = aiohttp.TCPConnector(limit=self.config.concurrent_requests * 2)
        
        async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
            # Create tasks
            tasks = []
            for i in range(self.config.total_requests):
                webhook_type = webhook_types[i % len(webhook_types)]
                task = bounded_request(session, webhook_type, i)
                tasks.append(task)
            
            # Execute tasks with progress reporting
            completed = 0
            for coro in asyncio.as_completed(tasks):
                result = await coro
                self.results.append(result)
                completed += 1
                
                if completed % 100 == 0:
                    print(f"📈 Progress: {completed}/{self.config.total_requests} requests completed")
        
        self.end_time = time.time()
        
        # Analyze results
        return self.analyze_results()
    
    def analyze_results(self) -> LoadTestResult:
        """Analyze load test results."""
        
        successful_requests = sum(1 for r in self.results if r["success"])
        failed_requests = len(self.results) - successful_requests
        
        # Calculate response times
        response_times = [r["response_time"] for r in self.results if r["response_time"]]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        # Calculate RPS
        total_duration = self.end_time - self.start_time
        requests_per_second = len(self.results) / total_duration if total_duration > 0 else 0
        
        # Error distribution
        error_distribution = {}
        for result in self.results:
            if not result["success"]:
                error = result["error"] or "unknown"
                error_distribution[error] = error_distribution.get(error, 0) + 1
        
        return LoadTestResult(
            total_requests=len(self.results),
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            requests_per_second=requests_per_second,
            error_distribution=error_distribution
        )
    
    def print_results(self, result: LoadTestResult) -> None:
        """Print load test results."""
        
        print("\n" + "="*60)
        print("📊 LOAD TEST RESULTS")
        print("="*60)
        
        print(f"🎯 Total Requests: {result.total_requests}")
        print(f"✅ Successful: {result.successful_requests} ({result.successful_requests/result.total_requests*100:.1f}%)")
        print(f"❌ Failed: {result.failed_requests} ({result.failed_requests/result.total_requests*100:.1f}%)")
        print()
        
        print("⏱️  Response Times:")
        print(f"   Average: {result.average_response_time*1000:.2f}ms")
        print(f"   Min: {result.min_response_time*1000:.2f}ms")
        print(f"   Max: {result.max_response_time*1000:.2f}ms")
        print()
        
        print(f"🚀 Requests/Second: {result.requests_per_second:.2f}")
        print()
        
        if result.error_distribution:
            print("❌ Error Distribution:")
            for error, count in result.error_distribution.items():
                print(f"   {error}: {count}")
        
        print("="*60)
        
        # Performance assessment
        success_rate = result.successful_requests / result.total_requests * 100
        
        if success_rate >= 99:
            print("🎉 EXCELLENT: >99% success rate")
        elif success_rate >= 95:
            print("👍 GOOD: >95% success rate")
        elif success_rate >= 90:
            print("⚠️  ACCEPTABLE: >90% success rate")
        else:
            print("💥 POOR: <90% success rate")
        
        if result.average_response_time < 0.1:
            print("⚡ FAST: <100ms average response time")
        elif result.average_response_time < 0.5:
            print("👍 GOOD: <500ms average response time")
        elif result.average_response_time < 1.0:
            print("⚠️  ACCEPTABLE: <1s average response time")
        else:
            print("🐌 SLOW: >1s average response time")


async def main():
    """Main function to run load test."""
    
    # Configuration
    config = LoadTestConfig(
        webhook_service_url="http://localhost:8012",
        shopify_secret="test_secret_key",
        concurrent_requests=50,
        total_requests=1000,
        request_delay_ms=10,
        timeout_seconds=30
    )
    
    # Create and run load tester
    tester = WebhookLoadTester(config)
    result = await tester.run_load_test()
    tester.print_results(result)


if __name__ == "__main__":
    asyncio.run(main())
