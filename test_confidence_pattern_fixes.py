#!/usr/bin/env python3
"""
Comprehensive test runner for confidence extraction and pattern creation fixes.

This script runs all relevant tests and validates that the fixes work correctly
without breaking existing functionality.
"""

import subprocess
import sys
import json
import tempfile
import asyncio
from pathlib import Path
from typing import Dict, List, Any

# Add app to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.services.recommendation import RecommendationService
from app.services.pattern_creator import PatternCreator
from app.llm.fakes import FakeLLMProvider
from app.config import Settings
from unittest.mock import MagicMock, AsyncMock


class ConfidencePatternFixValidator:
    """Validates that confidence and pattern creation fixes work correctly."""

    def __init__(self):
        self.results = {
            "confidence_tests": [],
            "pattern_tests": [],
            "integration_tests": [],
            "regression_tests": []
        }

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all validation tests."""
        print("🔍 Running Confidence and Pattern Creation Fix Validation")
        print("=" * 60)

        # Run unit tests first
        await self._run_unit_tests()
        
        # Run integration tests
        await self._run_integration_tests()
        
        # Run manual validation tests
        await self._run_manual_validation()
        
        # Run regression tests
        await self._run_regression_tests()

        return self._generate_report()

    async def _run_unit_tests(self):
        """Run existing unit tests for confidence and pattern creation."""
        print("\n📋 Running Unit Tests...")
        
        test_files = [
            "app/tests/unit/test_confidence_extraction.py",
            "app/tests/unit/test_pattern_creation_decision.py",
            "app/tests/unit/test_enhanced_pattern_creator.py",
            "app/tests/unit/test_pattern_creation_comprehensive.py"
        ]

        for test_file in test_files:
            if Path(test_file).exists():
                try:
                    result = subprocess.run(
                        ["python", "-m", "pytest", test_file, "-v"],
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    success = result.returncode == 0
                    self.results["confidence_tests" if "confidence" in test_file else "pattern_tests"].append({
                        "test": test_file,
                        "status": "PASS" if success else "FAIL",
                        "output": result.stdout if success else result.stderr
                    })
                    
                    print(f"  ✅ {test_file}: {'PASS' if success else 'FAIL'}")
                    
                except subprocess.TimeoutExpired:
                    print(f"  ⏰ {test_file}: TIMEOUT")
                    self.results["confidence_tests" if "confidence" in test_file else "pattern_tests"].append({
                        "test": test_file,
                        "status": "TIMEOUT",
                        "output": "Test timed out after 60 seconds"
                    })
            else:
                print(f"  ⚠️  {test_file}: NOT FOUND")

    async def _run_integration_tests(self):
        """Run integration tests."""
        print("\n🔗 Running Integration Tests...")
        
        integration_tests = [
            "app/tests/integration/test_confidence_integration.py",
            "app/tests/integration/test_confidence_pattern_e2e.py"
        ]

        for test_file in integration_tests:
            if Path(test_file).exists():
                try:
                    result = subprocess.run(
                        ["python", "-m", "pytest", test_file, "-v"],
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    
                    success = result.returncode == 0
                    self.results["integration_tests"].append({
                        "test": test_file,
                        "status": "PASS" if success else "FAIL",
                        "output": result.stdout if success else result.stderr
                    })
                    
                    print(f"  ✅ {test_file}: {'PASS' if success else 'FAIL'}")
                    
                except subprocess.TimeoutExpired:
                    print(f"  ⏰ {test_file}: TIMEOUT")
                    self.results["integration_tests"].append({
                        "test": test_file,
                        "status": "TIMEOUT",
                        "output": "Test timed out after 120 seconds"
                    })

    async def _run_manual_validation(self):
        """Run manual validation tests for specific scenarios."""
        print("\n🧪 Running Manual Validation Tests...")

        # Test confidence extraction with various formats
        await self._test_confidence_extraction_scenarios()
        
        # Test pattern creation with novel technologies
        await self._test_pattern_creation_scenarios()

    async def _test_confidence_extraction_scenarios(self):
        """Test confidence extraction with various LLM response formats."""
        print("  🎯 Testing Confidence Extraction Scenarios...")

        test_scenarios = [
            {
                "name": "Valid JSON with confidence",
                "llm_response": '{"confidence": 0.85, "feasibility": "Automatable"}',
                "expected_confidence": 0.85,
                "expected_source": "llm"
            },
            {
                "name": "Invalid confidence value",
                "llm_response": '{"confidence": "high", "feasibility": "Automatable"}',
                "expected_source": "pattern_based"
            },
            {
                "name": "Missing confidence",
                "llm_response": '{"feasibility": "Automatable"}',
                "expected_source": "pattern_based"
            },
            {
                "name": "Out of range confidence",
                "llm_response": '{"confidence": 1.5, "feasibility": "Automatable"}',
                "expected_confidence": 1.0,
                "expected_source": "llm"
            }
        ]

        for scenario in test_scenarios:
            try:
                # Setup fake LLM provider
                fake_llm = FakeLLMProvider()
                fake_llm.set_response(scenario["llm_response"])

                # Create mock services
                mock_settings = MagicMock()
                mock_embedding = MagicMock()
                mock_embedding.get_embedding = AsyncMock(return_value=[0.1] * 384)
                mock_embedding.search_similar = AsyncMock(return_value=[])

                pattern_creator = PatternCreator(mock_settings, fake_llm)
                service = RecommendationService(
                    settings=mock_settings,
                    llm_provider=fake_llm,
                    embedding_engine=mock_embedding,
                    pattern_creator=pattern_creator
                )

                # Test requirements
                requirements = {
                    "description": "Test scenario",
                    "business_domain": "test"
                }

                # Get recommendation
                result = await service.get_recommendation(requirements)

                # Validate results
                success = True
                error_msg = ""

                if "expected_confidence" in scenario:
                    if abs(result["confidence"] - scenario["expected_confidence"]) > 0.01:
                        success = False
                        error_msg = f"Expected confidence {scenario['expected_confidence']}, got {result['confidence']}"

                if result["confidence_source"] != scenario["expected_source"]:
                    success = False
                    error_msg = f"Expected source {scenario['expected_source']}, got {result['confidence_source']}"

                self.results["confidence_tests"].append({
                    "test": scenario["name"],
                    "status": "PASS" if success else "FAIL",
                    "output": error_msg if not success else "Confidence extraction working correctly"
                })

                print(f"    {'✅' if success else '❌'} {scenario['name']}: {'PASS' if success else 'FAIL'}")

            except Exception as e:
                self.results["confidence_tests"].append({
                    "test": scenario["name"],
                    "status": "ERROR",
                    "output": str(e)
                })
                print(f"    ❌ {scenario['name']}: ERROR - {e}")

    async def _test_pattern_creation_scenarios(self):
        """Test pattern creation with novel technologies."""
        print("  🏗️  Testing Pattern Creation Scenarios...")

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create existing pattern
            existing_pattern = {
                "pattern_id": "PAT-001",
                "name": "Traditional Web App",
                "description": "Standard web application",
                "tech_stack": ["PHP", "MySQL", "Apache"],
                "pattern_type": ["web_application"]
            }

            pattern_file = Path(temp_dir) / "PAT-001.json"
            with open(pattern_file, 'w') as f:
                json.dump(existing_pattern, f)

            test_scenarios = [
                {
                    "name": "Novel blockchain technologies",
                    "requirements": {
                        "description": "Blockchain supply chain tracking",
                        "tech_stack": ["Ethereum", "Solidity", "Web3.js"]
                    },
                    "llm_response": '{"action": "create", "pattern_id": "PAT-NEW-001", "confidence": 0.8}',
                    "should_create": True
                },
                {
                    "name": "Similar existing technology",
                    "requirements": {
                        "description": "Web application with database",
                        "tech_stack": ["PHP", "MySQL"]
                    },
                    "llm_response": '{"action": "enhance", "pattern_id": "PAT-001", "confidence": 0.75}',
                    "should_create": False
                }
            ]

            for scenario in test_scenarios:
                try:
                    # Setup fake LLM provider
                    fake_llm = FakeLLMProvider()
                    fake_llm.set_response(scenario["llm_response"])

                    # Create mock services
                    mock_settings = MagicMock()
                    mock_settings.pattern_library_path = temp_dir

                    mock_embedding = MagicMock()
                    mock_embedding.get_embedding = AsyncMock(return_value=[0.1] * 384)
                    mock_embedding.search_similar = AsyncMock(return_value=[])

                    pattern_creator = PatternCreator(mock_settings, fake_llm)
                    service = RecommendationService(
                        settings=mock_settings,
                        llm_provider=fake_llm,
                        embedding_engine=mock_embedding,
                        pattern_creator=pattern_creator
                    )

                    # Get recommendation
                    result = await service.get_recommendation(scenario["requirements"])

                    # Validate pattern creation decision
                    pattern_created = result.get("pattern_created", False)
                    success = pattern_created == scenario["should_create"]

                    self.results["pattern_tests"].append({
                        "test": scenario["name"],
                        "status": "PASS" if success else "FAIL",
                        "output": f"Pattern created: {pattern_created}, Expected: {scenario['should_create']}"
                    })

                    print(f"    {'✅' if success else '❌'} {scenario['name']}: {'PASS' if success else 'FAIL'}")

                except Exception as e:
                    self.results["pattern_tests"].append({
                        "test": scenario["name"],
                        "status": "ERROR",
                        "output": str(e)
                    })
                    print(f"    ❌ {scenario['name']}: ERROR - {e}")

    async def _run_regression_tests(self):
        """Run regression tests to ensure existing functionality works."""
        print("\n🔄 Running Regression Tests...")

        # Test that existing API endpoints still work
        regression_tests = [
            "app/tests/unit/test_recommendation.py",
            "app/tests/integration/test_complete_workflows.py"
        ]

        for test_file in regression_tests:
            if Path(test_file).exists():
                try:
                    result = subprocess.run(
                        ["python", "-m", "pytest", test_file, "-v"],
                        capture_output=True,
                        text=True,
                        timeout=90
                    )
                    
                    success = result.returncode == 0
                    self.results["regression_tests"].append({
                        "test": test_file,
                        "status": "PASS" if success else "FAIL",
                        "output": result.stdout if success else result.stderr
                    })
                    
                    print(f"  ✅ {test_file}: {'PASS' if success else 'FAIL'}")
                    
                except subprocess.TimeoutExpired:
                    print(f"  ⏰ {test_file}: TIMEOUT")

    def _generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report."""
        print("\n📊 Test Results Summary")
        print("=" * 60)

        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        error_tests = 0

        for category, tests in self.results.items():
            category_total = len(tests)
            category_passed = len([t for t in tests if t["status"] == "PASS"])
            category_failed = len([t for t in tests if t["status"] == "FAIL"])
            category_errors = len([t for t in tests if t["status"] in ["ERROR", "TIMEOUT"]])

            total_tests += category_total
            passed_tests += category_passed
            failed_tests += category_failed
            error_tests += category_errors

            print(f"\n{category.replace('_', ' ').title()}:")
            print(f"  Total: {category_total}")
            print(f"  Passed: {category_passed}")
            print(f"  Failed: {category_failed}")
            print(f"  Errors: {category_errors}")

        print(f"\nOverall Results:")
        print(f"  Total Tests: {total_tests}")
        print(f"  Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"  Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        print(f"  Errors: {error_tests} ({error_tests/total_tests*100:.1f}%)")

        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        overall_status = "PASS" if success_rate >= 0.9 and failed_tests == 0 else "FAIL"

        print(f"\nOverall Status: {'✅ PASS' if overall_status == 'PASS' else '❌ FAIL'}")

        return {
            "overall_status": overall_status,
            "success_rate": success_rate,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "error_tests": error_tests,
            "detailed_results": self.results
        }


async def main():
    """Main test runner."""
    validator = ConfidencePatternFixValidator()
    results = await validator.run_all_tests()
    
    # Save detailed results
    with open("confidence_pattern_fix_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: confidence_pattern_fix_results.json")
    
    # Exit with appropriate code
    sys.exit(0 if results["overall_status"] == "PASS" else 1)


if __name__ == "__main__":
    asyncio.run(main())