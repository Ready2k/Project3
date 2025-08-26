# Graphviz Installation Guide for Infrastructure Diagrams

## Overview

The AAA (Automated AI Assessment) system includes an **Infrastructure Diagram** feature that generates cloud architecture diagrams with vendor-specific icons (AWS, GCP, Azure). This feature uses the Python `diagrams` library, which requires **Graphviz** to be installed on your system.

## Error Symptoms

If you see any of these errors, you need to install Graphviz:

```
failed to execute WindowsPath('dot'), make sure the Graphviz executables are on your systems' PATH
```

```
Error generating infrastructure diagram: Graphviz is required for infrastructure diagrams
```

```
FileNotFoundError: [Errno 2] No such file or directory: 'dot'
```

## Installation Instructions

### Windows

**Option 1: Using Chocolatey (Recommended)**
```powershell
# Install Chocolatey if not already installed
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install Graphviz
choco install graphviz
```

**Option 2: Using winget**
```powershell
winget install graphviz
```

**Option 3: Manual Installation**
1. Download Graphviz from: https://graphviz.org/download/
2. Download the Windows installer (`.msi` file)
3. Run the installer and follow the setup wizard
4. **Important**: Make sure to check "Add Graphviz to system PATH" during installation
5. If you forgot to add to PATH, manually add `C:\Program Files\Graphviz\bin` to your system PATH

**Adding to PATH manually (if needed):**
1. Press `Win + R`, type `sysdm.cpl`, press Enter
2. Click "Environment Variables"
3. Under "System Variables", find and select "Path", click "Edit"
4. Click "New" and add: `C:\Program Files\Graphviz\bin`
5. Click "OK" to save all dialogs
6. Restart your command prompt/PowerShell

### macOS

**Using Homebrew (Recommended)**
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Graphviz
brew install graphviz
```

**Using MacPorts**
```bash
sudo port install graphviz
```

### Linux

**Ubuntu/Debian**
```bash
sudo apt-get update
sudo apt-get install graphviz
```

**CentOS/RHEL/Fedora**
```bash
# CentOS/RHEL
sudo yum install graphviz

# Fedora
sudo dnf install graphviz
```

**Arch Linux**
```bash
sudo pacman -S graphviz
```

## Verification

After installation, verify Graphviz is working:

```bash
dot -V
```

You should see output like:
```
dot - graphviz version 2.50.0 (20211204.2007)
```

## Troubleshooting

### Windows Issues

**Problem**: "dot is not recognized as an internal or external command"
**Solution**: Graphviz is not in your PATH. Follow the PATH setup instructions above.

**Problem**: Installation fails with permission errors
**Solution**: Run PowerShell or Command Prompt as Administrator.

**Problem**: Chocolatey not found
**Solution**: Install Chocolatey first using the command in the Windows section above.

### macOS Issues

**Problem**: "brew: command not found"
**Solution**: Install Homebrew first using the command in the macOS section above.

**Problem**: Permission denied errors
**Solution**: Make sure you have admin privileges or use `sudo` where indicated.

### Linux Issues

**Problem**: Package not found
**Solution**: Update your package manager first (`sudo apt-get update` or equivalent).

**Problem**: Permission denied
**Solution**: Make sure to use `sudo` for system package installation.

### General Issues

**Problem**: Still getting errors after installation
**Solution**: 
1. Restart your terminal/command prompt
2. Restart the AAA application
3. Verify installation with `dot -V`
4. Check that Graphviz bin directory is in your PATH

## Alternative Solutions

If you can't install Graphviz or prefer not to use Infrastructure Diagrams:

### Use Other Diagram Types
The AAA system offers several diagram types that don't require Graphviz:
- **Context Diagram**: System boundaries and external integrations
- **Container Diagram**: Internal components and services
- **Sequence Diagram**: Step-by-step process flows
- **Agent Interaction Diagram**: AI agent collaboration (for agentic systems)
- **Tech Stack Wiring Diagram**: Technology connections and data flows
- **C4 Diagram**: Standardized architecture documentation

### Docker Alternative
If you're using Docker, the provided Dockerfile already includes Graphviz:

```bash
# Build and run with Docker
docker-compose up
```

The Docker environment has Graphviz pre-installed and ready to use.

## How Infrastructure Diagrams Work

1. **LLM Generation**: The system uses your configured LLM (OpenAI, Claude, Bedrock) to analyze your requirements and generate a JSON specification for the infrastructure
2. **Python Code Generation**: The JSON spec is converted to Python code using the `diagrams` library
3. **Graphviz Rendering**: The `diagrams` library calls Graphviz's `dot` command to render the visual diagram
4. **Display**: The generated PNG/SVG image is displayed in the Streamlit interface

## Benefits of Infrastructure Diagrams

- **Vendor-Specific Icons**: Uses official AWS, GCP, Azure icons
- **Realistic Architecture**: Shows actual cloud services and patterns
- **Visual Blueprint**: Helps developers understand deployment architecture
- **Export Options**: Download as PNG or view generated Python code
- **Agentic AI Support**: Special handling for AI agent orchestration platforms

## Support

If you continue to have issues after following this guide:

1. Check the application logs for specific error messages
2. Verify your system meets the requirements
3. Try the Docker alternative if local installation fails
4. Use alternative diagram types that don't require Graphviz

The Infrastructure Diagram feature is optional - all other AAA functionality works without Graphviz.