# Pattern Color Guide

## Color Scheme Overview

The Pattern Library uses colored ball indicators to show the automation level and solution type at a glance:

- **🔴 Red**: Not Automatable / Manual processes
- **🟡 Yellow**: Partially Automatable / Traditional automation with human oversight  
- **🟢 Green**: Fully Automatable / AI-enhanced solutions
- **🔵 Blue**: Autonomous Agentic AI (APAT-*) - highest automation level

## Current Pattern Color Assignments

### 🔵 Autonomous Agentic AI Patterns (4)
| Pattern | Name | Automation Level |
|---------|------|------------------|
| APAT-001 | Autonomous Legal Contract Analysis Agent | Fully Autonomous (95%+ automation) |
| APAT-002 | Autonomous Invoice Processing and Payment Agent | Fully Autonomous (95%+ automation) |
| APAT-003 | Autonomous Customer Support Resolution Agent | Fully Autonomous (95%+ automation) |
| APAT-004 | Autonomous Payment Dispute Resolution Agent | Fully Autonomous (95%+ automation) |

### 🟢 Fully Automatable / AI-Enhanced Solutions (2)
| Pattern | Name | Feasibility | Key Features |
|---------|------|-------------|--------------|
| PAT-006 | PII Redaction & Data Loss Prevention Pipeline | Automatable | Automatic detection and redaction |
| PAT-009 | Enhanced AI Golf Swing Analysis and Autonomous Coaching Agent | AI-Enhanced | Autonomous coaching with AI analysis |

### 🟡 Partially Automatable / Traditional Automation (5)
| Pattern | Name | Feasibility | Human Oversight Required |
|---------|------|-------------|--------------------------|
| PAT-001 | Secure Legal Contract Summarization (On-Prem) | Partially Automatable | Human-in-the-loop legal review |
| PAT-002 | Invoice Intake, OCR, and ERP Posting | Traditional Automation | Manual verification steps |
| PAT-003 | Multilingual Support Ticket Processing | Partially Automatable | Human review for complex cases |
| PAT-004 | Brand-Tone Co‑Writing for Marketing Content | Partially Automatable | Human creative oversight |
| PAT-005 | Email Order Extraction & Fulfillment Orchestration | Partially Automatable | Manual approval workflows |

### 🔴 Not Automatable / Manual Processes (0)
Currently no patterns in this category - all patterns provide some level of automation benefit.

## Color Assignment Logic

The color assignment is based on:

1. **Pattern Type**: APAT-* patterns automatically get 🔵 blue (autonomous agents)
2. **Feasibility Field**: Direct mapping from pattern's feasibility assessment
3. **Content Analysis**: Keywords indicating automation level and human involvement
4. **Solution Architecture**: Traditional vs AI-enhanced vs autonomous approaches

## Visual Benefits

- **Quick Assessment**: Users can instantly see automation potential
- **Solution Categorization**: Clear distinction between traditional, AI, and agentic solutions
- **Decision Support**: Colors help users choose appropriate automation approaches
- **Progress Tracking**: Visual progression from manual → traditional → AI → autonomous

## Usage in UI

The colored balls appear:
- In Pattern Library listings
- In recommendation results
- In pattern analytics dashboards
- In export documents

This visual system helps users quickly identify the most appropriate automation solutions for their requirements.