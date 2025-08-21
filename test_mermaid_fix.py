#!/usr/bin/env python3
"""
Test script to validate Mermaid diagram generation fixes.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from streamlit_app import _validate_mermaid_syntax, _clean_mermaid_code, _sanitize

def test_mermaid_fixes():
    """Test the Mermaid diagram generation fixes."""
    
    print("Testing Mermaid diagram generation fixes...")
    
    # Test 1: Basic sanitization
    print("\n1. Testing sanitization:")
    test_labels = [
        "🤖 AI Agent",
        "User Request 👤",
        "Complex Agent (with special chars!)",
        "Agent-Name_123",
        ""
    ]
    
    for label in test_labels:
        sanitized = _sanitize(label)
        print(f"  '{label}' -> '{sanitized}'")
    
    # Test 2: Simple two-agent diagram
    print("\n2. Testing two-agent diagram generation:")
    simple_diagram = """flowchart TD
    U[User Request] --> A1[Agent_1]
    U --> A2[Agent_2]
    A1 <-->|Collaborate| A2
    A1 --> R[Coordinated Response]
    A2 --> R
    R --> U
    
    style A1 fill:#4ECDC4,stroke:#38B2AC,stroke-width:3px
    style A2 fill:#45B7D1,stroke:#3182CE,stroke-width:3px
    style R fill:#96CEB4,stroke:#68D391,stroke-width:2px
    style U fill:#FED7D7,stroke:#E53E3E,stroke-width:2px"""
    
    is_valid, error_msg = _validate_mermaid_syntax(simple_diagram)
    print(f"  Valid: {is_valid}")
    if not is_valid:
        print(f"  Error: {error_msg}")
    
    # Test 3: Cleaning problematic code
    print("\n3. Testing code cleaning:")
    problematic_code = """```mermaid
flowchart TD
    U[👤 User Request] --> A1[🤖 Agent 1]
    A1 --> R[🎯 Result]
```"""
    
    cleaned = _clean_mermaid_code(problematic_code)
    print(f"  Original length: {len(problematic_code)}")
    print(f"  Cleaned length: {len(cleaned)}")
    print(f"  First line: {cleaned.split(chr(10))[0] if cleaned else 'Empty'}")
    
    is_valid, error_msg = _validate_mermaid_syntax(cleaned)
    print(f"  Cleaned code valid: {is_valid}")
    if not is_valid:
        print(f"  Error: {error_msg}")
    
    # Test 4: Complex diagram structure
    print("\n4. Testing complex diagram validation:")
    complex_diagram = """flowchart TD
    U[User Request] --> C[Coordinator]
    C -->|Delegate| S1[Specialist_1]
    C -->|Delegate| S2[Specialist_2]
    C -->|Delegate| S3[Specialist_3]
    
    S1 <-->|Communicate| S2
    S2 <-->|Communicate| S3
    
    S1 --> R[Coordinated Solution]
    S2 --> R
    S3 --> R
    C --> R
    R --> U
    
    style C fill:#FF6B6B,stroke:#E53E3E,stroke-width:4px
    style S1 fill:#4ECDC4,stroke:#38B2AC,stroke-width:3px
    style S2 fill:#45B7D1,stroke:#3182CE,stroke-width:3px
    style S3 fill:#F7DC6F,stroke:#F1C40F,stroke-width:3px
    style R fill:#96CEB4,stroke:#68D391,stroke-width:2px
    style U fill:#FED7D7,stroke:#E53E3E,stroke-width:2px"""
    
    is_valid, error_msg = _validate_mermaid_syntax(complex_diagram)
    print(f"  Valid: {is_valid}")
    if not is_valid:
        print(f"  Error: {error_msg}")
    
    print("\n✅ Mermaid fix testing completed!")
    
    # Output a working example for manual testing
    print("\n📋 Working example for manual testing in mermaid.live:")
    print("=" * 50)
    print(simple_diagram)
    print("=" * 50)

if __name__ == "__main__":
    test_mermaid_fixes()