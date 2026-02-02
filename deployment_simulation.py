"""Deployment Simulation & Release Readiness Validation

Phase 3C-2: Comprehensive pre-deployment testing
This script simulates real-world deployment conditions without actual cloud deployment.

Tests:
1. Boot sequence validation
2. API contract verification
3. Failure mode simulation
4. Performance smoke test
5. Config & environment drift
"""

import os
import sys
import time
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import requests


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class DeploymentSimulator:
    """Simulates deployment conditions and validates system readiness"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.health_url = f"{base_url}/api/v1/health"  # Correct health endpoint path
        self.results = {
            "boot_sequence": [],
            "api_contracts": [],
            "failure_modes": [],
            "performance": [],
            "config_drift": [],
        }
        self.passed = 0
        self.failed = 0
        self.warnings = 0
    
    def log_success(self, message: str):
        """Log successful test"""
        print(f"{Colors.GREEN}✓{Colors.RESET} {message}")
        self.passed += 1
    
    def log_failure(self, message: str):
        """Log failed test"""
        print(f"{Colors.RED}✗{Colors.RESET} {message}")
        self.failed += 1
    
    def log_warning(self, message: str):
        """Log warning"""
        print(f"{Colors.YELLOW}⚠{Colors.RESET} {message}")
        self.warnings += 1
    
    def log_info(self, message: str):
        """Log info message"""
        print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")
    
    def section(self, title: str):
        """Print section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
        print(f"{Colors.BOLD}{title}{Colors.RESET}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 1. BOOT SEQUENCE VALIDATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_boot_sequence(self):
        """Test 1: Validate clean application startup"""
        self.section("TEST 1: BOOT SEQUENCE VALIDATION")
        
        # Check if server is running
        try:
            response = requests.get(self.health_url, timeout=5)
            if response.status_code == 200:
                self.log_success("Server is running and responsive")
                data = response.json()
                
                # Check health response structure
                required_fields = ["service_status", "uptime_seconds", "model_loaded"]
                for field in required_fields:
                    if field in data:
                        self.log_success(f"Health response contains '{field}'")
                    else:
                        self.log_failure(f"Health response missing '{field}'")
                
                # Check model status
                if data.get("model_loaded"):
                    self.log_success("ML model loaded successfully")
                else:
                    self.log_warning("ML model not loaded (degraded mode)")
                
                # Check status
                status = data.get("service_status")
                if status == "ok":
                    self.log_success("System status: ok")
                elif status == "degraded":
                    self.log_warning("System status: degraded")
                else:
                    self.log_failure(f"Unknown system status: {status}")
                    
            else:
                self.log_failure(f"Health check returned {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            self.log_failure("Cannot connect to server - is it running?")
            self.log_info("Start server with: uvicorn app.main:app --reload")
            return False
        except Exception as e:
            self.log_failure(f"Health check failed: {e}")
            return False
        
        # Check API version header
        try:
            response = requests.get(self.health_url)
            if "X-API-Version" in response.headers:
                version = response.headers["X-API-Version"]
                self.log_success(f"API version header present: {version}")
            else:
                self.log_warning("API version header missing")
        except Exception as e:
            self.log_failure(f"Failed to check API version: {e}")
        
        return True
    
    # ═══════════════════════════════════════════════════════════════════════
    # 2. API CONTRACT VERIFICATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_api_contracts(self):
        """Test 2: Verify all API endpoints match contracts"""
        self.section("TEST 2: API CONTRACT VERIFICATION")
        
        # Test 2.1: Valid prediction request
        self.log_info("Testing valid prediction request...")
        valid_payload = {
            "schema_version": "v1",
            "annual_income": 75000,
            "monthly_debt": 2000,
            "credit_score": 720,
            "loan_amount": 25000,
            "loan_term_months": 60,
            "employment_length_years": 5,
            "home_ownership": "MORTGAGE",
            "purpose": "debt_consolidation",
            "number_of_open_accounts": 10,
            "delinquencies_2y": 0,
            "inquiries_6m": 1,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/predict",
                json=valid_payload,
                timeout=35
            )
            
            if response.status_code == 200:
                self.log_success("Valid request accepted (200 OK)")
                data = response.json()
                
                # Check UX-safe wrapper fields
                required_ux_fields = ["status", "request_id", "model_version", 
                                     "prediction", "confidence", "error"]
                for field in required_ux_fields:
                    if field in data:
                        self.log_success(f"Response contains '{field}'")
                    else:
                        self.log_failure(f"Response missing '{field}'")
                
                # Verify response status
                if data.get("status") == "success":
                    self.log_success("Prediction status: success")
                    
                    # Check prediction values
                    if data.get("prediction") is not None:
                        pred = data["prediction"]
                        if 0.0 <= pred <= 1.0:
                            self.log_success(f"Prediction in valid range: {pred}")
                        else:
                            self.log_failure(f"Prediction out of range: {pred}")
                    
                    # Check data field
                    if data.get("data"):
                        detail_data = data["data"]
                        required_detail_fields = ["risk_score", "risk_level", 
                                                 "recommended_action", "model_version"]
                        for field in required_detail_fields:
                            if field in detail_data:
                                self.log_success(f"Detail data contains '{field}'")
                            else:
                                self.log_failure(f"Detail data missing '{field}'")
                else:
                    self.log_warning(f"Prediction status: {data.get('status')}")
                    if data.get("error"):
                        self.log_info(f"Error message: {data['error']}")
                        
            else:
                self.log_failure(f"Valid request returned {response.status_code}")
                self.log_info(f"Response: {response.text[:200]}")
                
        except Exception as e:
            self.log_failure(f"Prediction request failed: {e}")
        
        # Test 2.2: Invalid payload (missing required field)
        self.log_info("\nTesting invalid payload (missing field)...")
        invalid_payload = {
            "schema_version": "v1",
            "annual_income": 75000,
            # missing monthly_debt
            "credit_score": 720,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/predict",
                json=invalid_payload,
                timeout=5
            )
            
            if response.status_code == 422:
                self.log_success("Invalid request rejected (422 Unprocessable Entity)")
            else:
                self.log_failure(f"Invalid request returned {response.status_code} (expected 422)")
                
        except Exception as e:
            self.log_failure(f"Invalid payload test failed: {e}")
        
        # Test 2.3: Malformed JSON
        self.log_info("\nTesting malformed JSON...")
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/predict",
                data="not valid json",
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code in [400, 422]:
                self.log_success(f"Malformed JSON rejected ({response.status_code})")
            else:
                self.log_failure(f"Malformed JSON returned {response.status_code}")
                
        except Exception as e:
            self.log_failure(f"Malformed JSON test failed: {e}")
        
        # Test 2.4: Extra fields
        self.log_info("\nTesting extra fields (should be rejected)...")
        extra_fields_payload = {**valid_payload, "extra_field": "should_be_rejected"}
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/predict",
                json=extra_fields_payload,
                timeout=5
            )
            
            if response.status_code == 422:
                self.log_success("Extra fields rejected (422)")
            else:
                self.log_warning(f"Extra fields not rejected ({response.status_code})")
                
        except Exception as e:
            self.log_failure(f"Extra fields test failed: {e}")
        
        # Test 2.5: CORS headers
        self.log_info("\nTesting CORS headers...")
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/predict",
                json=valid_payload,
                headers={"Origin": "http://localhost:3000"},
                timeout=35
            )
            
            if "Access-Control-Allow-Origin" in response.headers:
                self.log_success("CORS headers present")
            else:
                self.log_warning("CORS headers missing")
                
        except Exception as e:
            self.log_failure(f"CORS test failed: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 3. FAILURE MODE SIMULATION
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_failure_modes(self):
        """Test 3: Simulate various failure conditions"""
        self.section("TEST 3: FAILURE MODE SIMULATION")
        
        # Test 3.1: NaN input
        self.log_info("Testing NaN input detection...")
        nan_payload = {
            "schema_version": "v1",
            "annual_income": float('nan'),
            "monthly_debt": 2000,
            "credit_score": 720,
            "loan_amount": 25000,
            "loan_term_months": 60,
            "employment_length_years": 5,
            "home_ownership": "MORTGAGE",
            "purpose": "debt_consolidation",
            "number_of_open_accounts": 10,
            "delinquencies_2y": 0,
            "inquiries_6m": 1,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/predict",
                json=nan_payload,
                timeout=5
            )
            
            # NaN should be caught by JSON serialization or validation
            if response.status_code in [400, 422]:
                self.log_success("NaN input rejected")
            else:
                data = response.json()
                if data.get("status") == "error" and "invalid" in data.get("error", "").lower():
                    self.log_success("NaN detected by input safety")
                else:
                    self.log_warning("NaN not properly detected")
                    
        except (ValueError, json.JSONDecodeError):
            # This is expected - JSON spec doesn't support NaN
            self.log_success("NaN rejected during JSON serialization (expected behavior)")
        except Exception as e:
            if "not JSON compliant" in str(e) or "nan" in str(e).lower():
                self.log_success("NaN rejected by JSON serialization (expected)")
            else:
                self.log_failure(f"NaN test failed: {e}")
        
        # Test 3.2: Out of range values
        self.log_info("\nTesting out-of-range values...")
        invalid_range_payload = {
            "schema_version": "v1",
            "annual_income": 100,  # Too low (minimum 1000)
            "monthly_debt": 2000,
            "credit_score": 250,  # Too low (minimum 300)
            "loan_amount": 25000,
            "loan_term_months": 60,
            "employment_length_years": 5,
            "home_ownership": "MORTGAGE",
            "purpose": "debt_consolidation",
            "number_of_open_accounts": 10,
            "delinquencies_2y": 0,
            "inquiries_6m": 1,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/predict",
                json=invalid_range_payload,
                timeout=5
            )
            
            # Pydantic may reject credit_score < 300 with 422
            if response.status_code == 422:
                self.log_success("Out-of-range values rejected by Pydantic (422)")
            elif response.status_code == 200:
                data = response.json()
                if data.get("status") == "error":
                    error_msg = data.get("error", "").lower()
                    if "invalid" in error_msg or "range" in error_msg or "low" in error_msg or "validation" in error_msg:
                        self.log_success("Out-of-range values detected by input safety")
                    else:
                        self.log_warning(f"Range validation unclear: {data.get('error')}")
                else:
                    self.log_warning("Out-of-range values not detected")
            else:
                self.log_failure(f"Unexpected status code: {response.status_code}")
                
        except Exception as e:
            self.log_failure(f"Range validation test failed: {e}")
        
        # Test 3.3: Invalid enum values
        self.log_info("\nTesting invalid enum values...")
        invalid_enum_payload = {
            "schema_version": "v1",
            "annual_income": 75000,
            "monthly_debt": 2000,
            "credit_score": 720,
            "loan_amount": 25000,
            "loan_term_months": 60,
            "employment_length_years": 5,
            "home_ownership": "INVALID_VALUE",  # Not in enum
            "purpose": "debt_consolidation",
            "number_of_open_accounts": 10,
            "delinquencies_2y": 0,
            "inquiries_6m": 1,
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/predict",
                json=invalid_enum_payload,
                timeout=5
            )
            
            if response.status_code == 422:
                self.log_success("Invalid enum value rejected (422)")
            else:
                self.log_failure(f"Invalid enum returned {response.status_code}")
                
        except Exception as e:
            self.log_failure(f"Enum validation test failed: {e}")
        
        # Test 3.4: Server stays alive after errors
        self.log_info("\nTesting server resilience after errors...")
        try:
            # Make a valid request after all the error tests
            valid_payload = {
                "schema_version": "v1",
                "annual_income": 75000,
                "monthly_debt": 2000,
                "credit_score": 720,
                "loan_amount": 25000,
                "loan_term_months": 60,
                "employment_length_years": 5,
                "home_ownership": "MORTGAGE",
                "purpose": "debt_consolidation",
                "number_of_open_accounts": 10,
                "delinquencies_2y": 0,
                "inquiries_6m": 1,
            }
            
            response = requests.post(
                f"{self.base_url}/api/v1/predict",
                json=valid_payload,
                timeout=35
            )
            
            if response.status_code == 200:
                self.log_success("Server still responsive after error handling")
            else:
                self.log_failure("Server degraded after errors")
                
        except Exception as e:
            self.log_failure(f"Resilience test failed: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 4. PERFORMANCE SMOKE TEST
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_performance(self):
        """Test 4: Basic performance smoke tests"""
        self.section("TEST 4: PERFORMANCE SMOKE TEST")
        
        valid_payload = {
            "schema_version": "v1",
            "annual_income": 75000,
            "monthly_debt": 2000,
            "credit_score": 720,
            "loan_amount": 25000,
            "loan_term_months": 60,
            "employment_length_years": 5,
            "home_ownership": "MORTGAGE",
            "purpose": "debt_consolidation",
            "number_of_open_accounts": 10,
            "delinquencies_2y": 0,
            "inquiries_6m": 1,
        }
        
        # Test 4.1: Sequential requests
        self.log_info("Testing 10 sequential requests...")
        latencies = []
        
        try:
            for i in range(10):
                start = time.time()
                response = requests.post(
                    f"{self.base_url}/api/v1/predict",
                    json=valid_payload,
                    timeout=35
                )
                latency = time.time() - start
                latencies.append(latency)
                
                if response.status_code != 200:
                    self.log_failure(f"Request {i+1} failed: {response.status_code}")
            
            if latencies:
                avg_latency = sum(latencies) / len(latencies)
                max_latency = max(latencies)
                min_latency = min(latencies)
                
                self.log_success(f"All 10 requests completed")
                self.log_info(f"  Avg latency: {avg_latency:.3f}s")
                self.log_info(f"  Min latency: {min_latency:.3f}s")
                self.log_info(f"  Max latency: {max_latency:.3f}s")
                
                # Check for latency growth
                first_half_avg = sum(latencies[:5]) / 5
                second_half_avg = sum(latencies[5:]) / 5
                growth = ((second_half_avg - first_half_avg) / first_half_avg) * 100
                
                if abs(growth) < 20:  # Less than 20% change
                    self.log_success(f"Latency stable (growth: {growth:.1f}%)")
                else:
                    self.log_warning(f"Latency growth detected: {growth:.1f}%")
                
                # Check timeout compliance
                if max_latency < 30:
                    self.log_success("All requests under 30s timeout")
                else:
                    self.log_warning(f"Max latency exceeds timeout: {max_latency:.1f}s")
                    
        except Exception as e:
            self.log_failure(f"Sequential request test failed: {e}")
        
        # Test 4.2: Response time for health check
        self.log_info("\nTesting health check response time...")
        try:
            health_latencies = []
            for _ in range(5):
                start = time.time()
                response = requests.get(self.health_url, timeout=5)
                latency = time.time() - start
                health_latencies.append(latency)
            
            avg_health_latency = sum(health_latencies) / len(health_latencies)
            
            if avg_health_latency < 0.1:  # 100ms
                self.log_success(f"Health check fast: {avg_health_latency*1000:.1f}ms")
            elif avg_health_latency < 3.0:  # 3 seconds (acceptable with model loading)
                self.log_info(f"Health check acceptable: {avg_health_latency*1000:.1f}ms")
            else:
                self.log_warning(f"Health check slow: {avg_health_latency*1000:.1f}ms")
                
        except Exception as e:
            self.log_failure(f"Health check performance test failed: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # 5. CONFIG & ENVIRONMENT DRIFT CHECK
    # ═══════════════════════════════════════════════════════════════════════
    
    def test_config_drift(self):
        """Test 5: Verify config handling and defaults"""
        self.section("TEST 5: CONFIG & ENVIRONMENT DRIFT CHECK")
        
        # Check .env.example exists and is complete
        self.log_info("Checking .env.example completeness...")
        env_example_path = Path(".env.example")
        
        if env_example_path.exists():
            self.log_success(".env.example exists")
            
            content = env_example_path.read_text()
            required_sections = [
                "APP_NAME",
                "ENVIRONMENT",
                "LOG_LEVEL",
                "CORS",
                "MODEL_PATH",
            ]
            
            for section in required_sections:
                if section in content:
                    self.log_success(f"  {section} documented")
                else:
                    self.log_warning(f"  {section} missing from .env.example")
        else:
            self.log_failure(".env.example not found")
        
        # Check model files exist
        self.log_info("\nChecking model artifacts...")
        model_paths = [
            Path("models/credit_risk_model.pkl"),
            Path("models/metadata.json"),
        ]
        
        for path in model_paths:
            if path.exists():
                self.log_success(f"  {path} exists")
            else:
                self.log_warning(f"  {path} not found (will use rule-based fallback)")
        
        # Test health endpoint in degraded mode awareness
        self.log_info("\nTesting degraded mode detection...")
        try:
            response = requests.get(self.health_url, timeout=5)
            data = response.json()
            
            if "model_loaded" in data:
                if data["model_loaded"]:
                    self.log_success("System reports model loaded")
                else:
                    self.log_warning("System in degraded mode (no ML model)")
                    
                    # In degraded mode, status should be "degraded"
                    if data.get("service_status") == "degraded":
                        self.log_success("Degraded mode correctly reported")
                    else:
                        self.log_warning(f"Status is '{data.get('service_status')}' but model not loaded")
            else:
                self.log_failure("Health response doesn't report model status")
                
        except Exception as e:
            self.log_failure(f"Degraded mode test failed: {e}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════════
    
    def print_summary(self):
        """Print test summary"""
        self.section("DEPLOYMENT SIMULATION SUMMARY")
        
        total = self.passed + self.failed
        pass_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"Total Tests: {total}")
        print(f"{Colors.GREEN}Passed: {self.passed}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {self.failed}{Colors.RESET}")
        print(f"{Colors.YELLOW}Warnings: {self.warnings}{Colors.RESET}")
        print(f"\nPass Rate: {pass_rate:.1f}%\n")
        
        if self.failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ DEPLOYMENT SIMULATION PASSED{Colors.RESET}")
            print(f"{Colors.GREEN}System is ready for release{Colors.RESET}\n")
            return True
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ DEPLOYMENT SIMULATION FAILED{Colors.RESET}")
            print(f"{Colors.RED}Fix failing tests before deployment{Colors.RESET}\n")
            return False
    
    def run_all_tests(self):
        """Run all deployment simulation tests"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}")
        print("╔═══════════════════════════════════════════════════════════╗")
        print("║     DEPLOYMENT SIMULATION & RELEASE READINESS CHECK       ║")
        print("║                    Phase 3C-2                             ║")
        print("╚═══════════════════════════════════════════════════════════╝")
        print(f"{Colors.RESET}\n")
        
        # Run all test suites
        server_running = self.test_boot_sequence()
        
        if server_running:
            self.test_api_contracts()
            self.test_failure_modes()
            self.test_performance()
            self.test_config_drift()
        else:
            self.log_failure("Cannot proceed - server not running")
            self.log_info("Start server with: uvicorn app.main:app")
        
        # Print summary
        return self.print_summary()


def main():
    """Main entry point"""
    simulator = DeploymentSimulator()
    success = simulator.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
