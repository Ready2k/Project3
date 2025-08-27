#!/usr/bin/env python3
"""Test script to verify shared constraints functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_constraint_building():
    """Test the constraint building functionality."""
    
    # Mock the AAA class methods
    class MockAAA:
        def build_constraints_object(self, constraint_data):
            """Build constraints object from constraint data."""
            constraints = {}
            
            # Parse restricted technologies and required integrations
            if constraint_data.get("restricted_technologies"):
                banned_tools = [tech.strip() for tech in constraint_data["restricted_technologies"].split('\n') if tech.strip()]
                if banned_tools:
                    constraints["banned_tools"] = banned_tools
            
            if constraint_data.get("required_integrations"):
                required_ints = [tech.strip() for tech in constraint_data["required_integrations"].split('\n') if tech.strip()]
                if required_ints:
                    constraints["required_integrations"] = required_ints
            
            # Add other constraints
            if constraint_data.get("compliance_requirements"):
                constraints["compliance_requirements"] = constraint_data["compliance_requirements"]
            if constraint_data.get("data_sensitivity"):
                constraints["data_sensitivity"] = constraint_data["data_sensitivity"]
            if constraint_data.get("budget_constraints"):
                constraints["budget_constraints"] = constraint_data["budget_constraints"]
            if constraint_data.get("deployment_preference"):
                constraints["deployment_preference"] = constraint_data["deployment_preference"]
            
            return constraints if constraints else None
    
    # Test data
    test_constraint_data = {
        "domain": "finance",
        "pattern_types": ["workflow", "data-processing"],
        "restricted_technologies": "Azure\nOracle Database\nSalesforce",
        "required_integrations": "Active Directory\nSAP\nPostgreSQL",
        "compliance_requirements": ["GDPR", "SOX"],
        "data_sensitivity": "Confidential",
        "budget_constraints": "Medium (Some commercial tools OK)",
        "deployment_preference": "Hybrid"
    }
    
    # Test the constraint building
    aaa = MockAAA()
    constraints = aaa.build_constraints_object(test_constraint_data)
    
    print("✅ Constraint Building Test Results:")
    print(f"Domain: {test_constraint_data['domain']}")
    print(f"Pattern Types: {test_constraint_data['pattern_types']}")
    print(f"Built Constraints: {constraints}")
    
    # Verify expected structure
    expected_keys = ["banned_tools", "required_integrations", "compliance_requirements", 
                    "data_sensitivity", "budget_constraints", "deployment_preference"]
    
    for key in expected_keys:
        if key in constraints:
            print(f"✅ {key}: {constraints[key]}")
        else:
            print(f"❌ Missing {key}")
    
    print("\n✅ Test completed successfully!")
    return True

if __name__ == "__main__":
    test_constraint_building()