# User Guide

Complete guide to using the Automated AI Assessment (AAA) system for evaluating requirements for autonomous agentic AI implementation.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Analysis Workflow](#analysis-workflow)
3. [Input Methods](#input-methods)
4. [Understanding Results](#understanding-results)
5. [Diagram Generation](#diagram-generation)
6. [Pattern Management](#pattern-management)
7. [Technology Catalog](#technology-catalog)
8. [Export Options](#export-options)
9. [Advanced Features](#advanced-features)

## Getting Started

### Prerequisites

- Web browser (Chrome, Firefox, Safari, Edge)
- Access to the AAA system (local installation or hosted instance)
- LLM provider API key (OpenAI, Anthropic, or AWS Bedrock)

### Initial Setup

1. **Access the System**
   - Navigate to the Streamlit interface (typically http://localhost:8500)
   - The system will load with the main Analysis tab active

2. **Configure LLM Provider** (Sidebar)
   - Select your preferred provider: OpenAI, Bedrock, Claude, Internal, or FakeLLM
   - Enter your API key in the secure input field
   - Select the appropriate model for your use case
   - Click "Test Connection" to verify setup

3. **Verify System Status**
   - Check the connection status indicator
   - Review any configuration warnings or errors
   - Ensure all required services are running

## Analysis Workflow

The AAA system follows a structured workflow to assess your requirements:

### Phase 1: Requirement Ingestion
- Submit your automation requirement
- System parses and validates the input
- Initial session creation and state management

### Phase 2: Q&A Clarification
- AI generates contextual questions based on your requirement
- Answer questions to provide additional context
- System validates and processes your responses

### Phase 3: Pattern Matching
- Tag-based filtering of relevant patterns
- Vector similarity search using FAISS
- Intelligent ranking and selection of best matches

### Phase 4: Technology Analysis
- LLM-driven tech stack generation
- Constraint application and filtering
- Technology categorization and descriptions

### Phase 5: Recommendation Generation
- Comprehensive feasibility assessment
- Confidence scoring and analysis
- Implementation guidance creation

### Phase 6: Export and Documentation
- Multi-format export generation
- Diagram creation and rendering
- Complete analysis documentation

## Input Methods

### Text Input
**Best for:** Simple requirements, quick assessments, proof of concepts

1. Select "Text Input" from the input method dropdown
2. Enter your requirement description in the text area
3. Optionally specify:
   - Domain (e.g., customer_support, data_processing)
   - Pattern types to focus on
   - Technology constraints
4. Click "🚀 Analyze Requirements"

**Example:**
```
I need to automate customer support ticket processing with AI analysis. 
The system should categorize tickets, suggest responses, and escalate 
complex issues to human agents.
```

### File Upload
**Best for:** Detailed requirements, specifications, user stories

1. Select "File Upload" from the input method dropdown
2. Click "Browse files" or drag and drop your file
3. Supported formats: TXT, MD, PDF, DOCX
4. The system will extract and parse the content
5. Review the extracted text and proceed with analysis

**Supported File Types:**
- `.txt` - Plain text files
- `.md` - Markdown documents
- `.pdf` - PDF documents (text extraction)
- `.docx` - Word documents

### Jira Integration
**Best for:** Existing Jira tickets, team workflows, enterprise environments

1. Select "Jira Integration" from the input method dropdown
2. Configure Jira connection (if not already set up):
   - Base URL (e.g., https://your-domain.atlassian.net)
   - Authentication (email + API token or personal access token)
3. Enter the Jira ticket key (e.g., PROJ-123)
4. System fetches ticket details and processes the requirement
5. Review extracted information and proceed

**Jira Configuration:**
- **Jira Cloud**: Use email + API token authentication
- **Jira Data Center**: Use personal access token authentication
- **SSL Issues**: System includes SSL bypass options for corporate environments

### Resume Previous Session
**Best for:** Continuing interrupted analyses, sharing results, collaboration

1. Select "Resume Previous Session" from the input method dropdown
2. Enter the session ID (UUID format)
3. System validates and loads the previous session
4. Continue from where you left off

**Finding Session IDs:**
- Progress tracking section during analysis
- Analysis results page
- Export files (JSON/Markdown headers)
- Browser URL during active sessions
- Shared links from team members

## Understanding Results

### Feasibility Assessment

The system provides a comprehensive assessment with color-coded feasibility levels:

- **🟢 Fully Automatable**: Complete automation possible with high confidence
- **🟡 Partially Automatable**: Some automation possible, human oversight required
- **🔴 Not Automatable**: Current requirement not suitable for automation
- **🔵 Needs Clarification**: Insufficient information to make determination

### Assessment Components

#### 🔍 Key Insights
Important observations from AI analysis of your requirement:
- Business process complexity
- Data availability and quality
- Integration requirements
- Regulatory considerations

#### ⚠️ Automation Challenges
Potential obstacles and considerations:
- Technical limitations
- Integration complexity
- Data quality issues
- Regulatory compliance
- Change management needs

#### 🎯 Recommended Approach
Specific implementation strategy:
- Architecture recommendations
- Technology stack suggestions
- Implementation phases
- Risk mitigation strategies

#### 📋 Next Steps
Actionable items to move forward:
- Immediate actions
- Planning activities
- Resource requirements
- Timeline considerations

#### 📊 Confidence Level
AI's confidence in the assessment (0-100%):
- **90-100%**: High confidence, clear path forward
- **70-89%**: Good confidence, minor uncertainties
- **50-69%**: Moderate confidence, some risks
- **Below 50%**: Low confidence, significant unknowns

### Pattern Matches

The system shows matched patterns with relevance scores:

#### Traditional Patterns (PAT-*)
- Established automation patterns
- Proven implementation approaches
- Lower autonomy levels (60-80%)

#### Agentic Patterns (APAT-*)
- Autonomous agent solutions
- Advanced reasoning capabilities
- Higher autonomy levels (95-98%)

#### Pattern Information
- **Relevance Score**: How well the pattern matches your requirement
- **Autonomy Level**: Degree of autonomous operation
- **Complexity**: Implementation difficulty
- **Tech Stack**: Required technologies

### Technology Recommendations

#### Categorized Technologies
Technologies are organized into logical categories:
- **Programming Languages**: Core development languages
- **Web Frameworks & APIs**: Application frameworks
- **Databases & Storage**: Data persistence solutions
- **Cloud & Infrastructure**: Hosting and deployment
- **AI & Machine Learning**: AI/ML frameworks and services
- **Communication & Integration**: External system connections

#### Technology Details
Each technology includes:
- **Purpose**: Why this technology is recommended
- **Use Case**: How it fits your specific requirement
- **Alternatives**: Other options to consider
- **Integration**: How it connects with other components

## Diagram Generation

### Available Diagram Types

#### Context Diagram
**Purpose**: Shows system boundaries and external integrations
- External actors and systems
- High-level data flows
- System boundaries
- Key relationships

#### Container Diagram
**Purpose**: Internal components and data flow
- Application components
- Databases and storage
- Internal communication
- Technology boundaries

#### Sequence Diagram
**Purpose**: Step-by-step process flow with decision points
- Process steps and timing
- Decision points and branches
- Actor interactions
- Error handling flows

#### C4 Architecture Diagram
**Purpose**: Proper C4 architecture model using standardized syntax
- Standardized C4 notation
- System context and containers
- Official C4 model compliance
- Professional architecture documentation

#### Infrastructure Diagram
**Purpose**: Cloud architecture with vendor-specific icons
- AWS, GCP, Azure components
- Network topology
- Security boundaries
- Resource relationships

#### Tech Stack Wiring Diagram
**Purpose**: Technical component connections and data flows
- Component interactions
- API connections and protocols
- Data flow directions
- Integration points

### Diagram Features

#### Enhanced Viewing Options
- **Full-size Browser View**: Open diagrams in new browser tab
- **Interactive Controls**: Zoom, pan, and navigate large diagrams
- **Print Support**: High-quality printing with proper scaling
- **SVG Download**: Vector format for presentations

#### Draw.io Export
- **Professional Editing**: Export to Draw.io for customization
- **Team Collaboration**: Share editable diagrams with team
- **Presentation Ready**: Create polished diagrams for stakeholders
- **Format Compatibility**: Works with all diagram types

#### Mermaid Live Editor
- **Code Editing**: Direct link to Mermaid Live Editor
- **Syntax Validation**: Real-time syntax checking
- **Theme Options**: Multiple visual themes available
- **Export Options**: PNG, SVG, PDF export from editor

## Pattern Management

### Pattern Library Overview

The system includes two types of patterns:

#### Traditional Patterns (PAT-001 to PAT-006)
- Established automation approaches
- Human-assisted workflows
- Moderate autonomy levels
- Proven implementation paths

#### Agentic Patterns (APAT-001 to APAT-005)
- Autonomous agent solutions
- AI-driven decision making
- High autonomy levels (95-98%)
- Advanced reasoning capabilities

### Pattern Analytics

Access pattern performance data through the **Pattern Analytics** tab:

#### Usage Metrics
- **Match Frequency**: How often patterns are matched
- **Success Rate**: Pattern implementation success
- **User Feedback**: Quality ratings and comments
- **Trend Analysis**: Usage patterns over time

#### Filtering Options
- **Time Periods**: Current session, 24 hours, 7 days, all time
- **Pattern Types**: Traditional, agentic, or all patterns
- **Domains**: Filter by business domain
- **Confidence Levels**: Filter by assessment confidence

#### Pattern Details
- **Pattern Information**: Complete pattern metadata
- **Match History**: Recent matches and contexts
- **Performance Metrics**: Success rates and feedback
- **Related Patterns**: Similar or complementary patterns

### Pattern Enhancement

The system can enhance existing patterns instead of creating duplicates:

#### Conceptual Similarity Detection
- Analyzes business process overlap
- Evaluates domain alignment
- Compares pattern types and feasibility
- Prevents unnecessary duplication

#### Smart Enhancement Process
- Merges complementary technologies
- Extends pattern capabilities
- Adds integration requirements
- Maintains pattern quality

## Technology Catalog

### Catalog Overview

The system maintains a comprehensive catalog of 60+ technologies across 18+ categories:

#### Technology Categories
- **Agentic AI & Multi-Agent Systems**: LangChain, CrewAI, AutoGen
- **AI & Machine Learning**: OpenAI, Claude, HuggingFace
- **Programming Languages**: Python, Node.js, Java, TypeScript
- **Web Frameworks & APIs**: FastAPI, Django, Express, Spring
- **Databases & Storage**: PostgreSQL, MongoDB, Redis, ElasticSearch
- **Cloud & Infrastructure**: AWS, Azure, GCP, Docker, Kubernetes
- **And 12 more specialized categories...**

### Technology Management

#### Viewing Technologies
- **Category Filtering**: Browse by technology category
- **Search Functionality**: Find technologies by name, description, or tags
- **Maturity Filtering**: Filter by technology maturity level
- **License Filtering**: Filter by license type (open source, commercial)

#### Technology Details
Each technology includes:
- **Name and Description**: Clear identification and purpose
- **Category and Tags**: Organization and searchability
- **Maturity Level**: Experimental, stable, mature, legacy
- **License Information**: Open source, commercial, enterprise
- **Alternatives**: Similar or competing technologies
- **Integrations**: Compatible technologies and frameworks
- **Use Cases**: Common implementation scenarios

#### Catalog Management
- **Automatic Updates**: LLM-suggested technologies added automatically
- **Manual Curation**: Add, edit, or remove technologies
- **Backup Safety**: Automatic backups before modifications
- **Import/Export**: Share catalogs between environments

## Export Options

### Export Formats

#### JSON Export
**Best for:** API integration, data processing, automation
- Complete analysis data
- Structured format for processing
- Session metadata included
- Technology and pattern details

#### Markdown Export
**Best for:** Documentation, reports, sharing with teams
- Human-readable format
- Formatted sections and headers
- Easy to edit and customize
- Version control friendly

#### Interactive HTML Export
**Best for:** Presentations, stakeholder reviews, archival
- Self-contained HTML file
- Interactive elements and navigation
- Professional styling and layout
- No external dependencies

### Export Content

All export formats include:
- **Session Information**: ID, timestamp, configuration
- **Requirements**: Original input and processed requirements
- **Q&A Responses**: Questions asked and answers provided
- **Pattern Matches**: Matched patterns with relevance scores
- **Technology Stack**: Recommended technologies with descriptions
- **Feasibility Assessment**: Complete analysis and recommendations
- **Confidence Metrics**: Assessment confidence and scoring

### Export Usage

#### Sharing Results
- **Team Collaboration**: Share analysis with team members
- **Stakeholder Reviews**: Present findings to decision makers
- **Documentation**: Include in project documentation
- **Archival**: Maintain records of analysis decisions

#### Integration
- **API Processing**: Use JSON exports for automated processing
- **Report Generation**: Include in automated reporting systems
- **Data Analysis**: Analyze patterns and trends across assessments
- **Audit Trails**: Maintain compliance and decision records

## Advanced Features

### Session Management

#### Session Persistence
- **Automatic Saving**: All progress automatically saved
- **Session Recovery**: Resume interrupted analyses
- **Cross-Device Access**: Access sessions from different devices
- **Session Sharing**: Share session IDs with team members

#### Session Information
- **Unique Identifiers**: UUID-based session identification
- **Timestamp Tracking**: Creation and modification times
- **Progress Tracking**: Current phase and completion status
- **Configuration Snapshot**: LLM provider and model used

### Technology Constraints

#### Enterprise Constraints
- **Banned Technologies**: Specify technologies that cannot be used
- **Required Integrations**: Must work with existing systems
- **Compliance Requirements**: GDPR, HIPAA, SOX, PCI-DSS, etc.
- **Data Sensitivity**: Public, internal, confidential, restricted
- **Budget Constraints**: Open source preferred vs enterprise solutions
- **Deployment Preferences**: Cloud-only, on-premises, hybrid

#### Constraint Application
- **LLM Context**: Constraints included in AI prompts
- **Technology Filtering**: Banned technologies automatically excluded
- **Pattern Selection**: Compliance requirements considered
- **Results Display**: Applied constraints shown in recommendations

### System Configuration

#### Configurable Parameters
- **Autonomy Assessment**: Thresholds, scoring weights, classification
- **Pattern Matching**: Tag/vector weights, similarity thresholds
- **LLM Generation**: Temperature, max tokens, penalties, timeouts
- **Recommendations**: Confidence thresholds, boost factors

#### Configuration Management
- **Real-time Adjustment**: Modify parameters with live validation
- **Import/Export**: Share configurations across environments
- **Reset to Defaults**: Quick restoration of original values
- **Configuration Preview**: Live YAML preview of current settings

### Security Features

#### Advanced Prompt Defense
- **Multi-layered Protection**: 8 specialized attack detectors
- **Real-time Monitoring**: Continuous threat assessment
- **User Education**: Contextual guidance for security violations
- **Audit Logging**: Complete security event tracking

#### Input Validation
- **Comprehensive Sanitization**: Multi-stage input cleaning
- **Schema Validation**: Structured data validation
- **Business Logic Protection**: Configuration access controls
- **Error Boundary Handling**: Graceful error recovery

### Observability

#### System Monitoring
- **API Performance**: Request/response times and throughput
- **LLM Usage**: Provider usage and performance metrics
- **Error Tracking**: Error rates and failure patterns
- **Resource Utilization**: Memory, CPU, and storage usage

#### LLM Message Audit
- **Complete Transparency**: All LLM prompts and responses logged
- **Purpose Filtering**: Filter by operation type
- **Security Events**: Security-related LLM interactions
- **Performance Analysis**: Response times and token usage

## Troubleshooting

### Common Issues

#### Connection Problems
- **LLM Provider Errors**: Check API keys and network connectivity
- **Timeout Issues**: Verify timeout settings and network stability
- **SSL Certificate Problems**: Corporate firewall or proxy issues

#### Analysis Issues
- **No Pattern Matches**: Requirement may be too vague or specific
- **Low Confidence Scores**: Provide more detailed requirements
- **Missing Technologies**: Check technology catalog completeness

#### Performance Issues
- **Slow Response Times**: Check system resources and network
- **Memory Issues**: Clear cache or restart services
- **High CPU Usage**: Monitor concurrent analyses and optimize

### Getting Help

#### Documentation Resources
- **User Guide**: This comprehensive guide
- **API Documentation**: Technical API reference
- **Architecture Guide**: System design and components
- **Security Guide**: Security features and best practices

#### Support Channels
- **System Logs**: Check application logs for error details
- **Debug Mode**: Enable debug mode for detailed troubleshooting
- **Configuration Review**: Verify system configuration settings
- **Community Resources**: Check project documentation and issues

### Best Practices

#### Requirement Writing
- **Be Specific**: Provide detailed, specific requirements
- **Include Context**: Business context and constraints
- **Define Success**: Clear success criteria and metrics
- **Consider Constraints**: Technology, budget, and compliance limitations

#### System Usage
- **Regular Updates**: Keep technology catalog current
- **Pattern Maintenance**: Review and update patterns regularly
- **Security Awareness**: Follow security best practices
- **Performance Monitoring**: Monitor system performance and usage

#### Team Collaboration
- **Session Sharing**: Use session IDs for collaboration
- **Export Standards**: Establish export format standards
- **Configuration Management**: Maintain consistent configurations
- **Knowledge Sharing**: Share patterns and best practices