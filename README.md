# UVLLM RTL Repair Framework

## Project Overview
UVLLM is a framework designed to repair RTL (Register Transfer Level) code by automating the processes of detection, localization, and correction of errors in hardware designs. The framework supports preprocessing, simulation, repair, and VCD file analysis for Verilog files.

## Directory Structure
```
UVLLM/
├── api.py                # OpenAI API integration module
├── Config.py             # Configuration file handling module
├── Main.py               # Main script for workflow control
├── Repair.py             # Repair module with error localization and correction logic
├── Benchmark/            # Benchmark-related modules
├── Locator/              # Error localization modules
├── rtlrepair/            # RTL repair modules
├── utils/                # Utility modules, including VCD file analysis tools
├── VerilogAnalyzer/      # Verilog file analysis modules
ErrorSet/
├── accu/                 # Contains Verilog files and data for the accu benchmark
├── adder_16bit/          # Contains Verilog files and data for the adder_16bit benchmark
├── ...                   # Additional benchmark folders
logs/                     # Directory for log files
workdir/                  # Working directory for intermediate files
patch/                    # Directory for storing repaired files
verilator/                # Verilator tool-related files
```

## Installation and Environment Setup
### Dependencies
- Python 3.8 or higher
- Verilator
- pip package dependencies (see `requirements.txt`)

### Installation Steps
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd UVLLM
   ```

2. Create a virtual environment and install dependencies:
   ```bash
   bash venv_setup.sh
   ```

3. Install Verilator:
   ```bash
   sudo apt-get install verilator
   ```

## Usage Guide
### Running the Main Script
The main script `Main.py` serves as the entry point for the framework. It supports the following command-line arguments:
- `-b`: Benchmark folder (e.g., `ErrorSet`)
- `-p`: Project name (e.g., `accu`)
- `-v`: Version number (e.g., `1`)

Example:
```bash
python3 UVLLM/Main.py -b ErrorSet -p accu -v 1
```

### Repair Workflow
1. **Preprocessing**:
   - Check for syntax errors in Verilog files.
   - Generate intermediate files.

2. **Error Localization**:
   - Parse Abstract Syntax Tree (AST).
   - Analyze dataflow to identify suspicious code lines.

3. **Repair**:
   - Generate repair patches based on localization results.
   - Validate the effectiveness of the repair.

4. **Simulation and Analysis**:
   - Simulate using Verilator.
   - Analyze the generated VCD files.

## Common Issues
### Verilator Not Found
Ensure Verilator is installed and available in the system path:
```bash
sudo apt-get install verilator
```

### Verilog File Syntax Errors
Check the Verilog files in the benchmark folder and fix any syntax issues.

### File Path Errors
Ensure the path settings in `Config.py` are correct.

## Contribution
Feel free to submit issues and contribute code!

## License
This project is open-source under the MIT License.

### Setting Up API Key
To use the OpenAI API, set the `OPENAI_API_KEY` environment variable. You can do this by adding the following line to your shell configuration file (e.g., `.bashrc` or `.zshrc`):

```bash
export OPENAI_API_KEY="your-api-key-here"
```

After setting the environment variable, reload your shell configuration:

```bash
source ~/.bashrc  # or source ~/.zshrc
```
