# Guacamole CSV Import Tool

This tool allows you to import connections from a CSV file into Apache Guacamole.

## Features

- Import connections from a CSV file into Apache Guacamole
- Automatically create connection groups based on site paths
- Environment variable configuration for Guacamole API credentials
- Command-line argument support for specifying the CSV file

## Requirements

- Python 3.12 or higher
- pipenv (for dependency management)
- Apache Guacamole server

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd guacamole-installation-guide
   ```

2. Install dependencies using pipenv:
   ```
   pipenv install
   ```

3. Configure your environment variables by copying the example file and editing it:
   ```
   cp .env.example .env
   ```
   Then edit the `.env` file with your Guacamole API credentials.

## Usage

Run the script with pipenv:

```
pipenv run python import_from_csv_refactored.py --csv your_file.csv
```

Or if you prefer to use the executable directly:

```
./import_from_csv_refactored.py --csv your_file.csv
```

If no CSV file is specified, the script will default to `connections.csv` in the current directory.

## CSV Format

The CSV file should have the following columns:

- `site`: The path for the connection group hierarchy (e.g., "AIN/DC1/Rack10")
- `device_name`: The name of the connection
- `protocol`: The protocol to use (e.g., "ssh", "vnc", "rdp")
- `hostname`: The hostname or IP address of the target device
- `username`: The username for authentication
- `password`: The password for authentication
- `port`: (Optional) The port to connect to (defaults to 22 for SSH)

## Project Structure

- `import_from_csv_refactored.py`: Entry point script
- `src/`: Package containing the refactored code
  - `main.py`: Main function and CSV processing logic
  - `connection_group_tree.py`: Class for managing connection group tree structure
  - `guacamole_api.py`: Class for interacting with the Guacamole API
- `.env`: Environment variables for configuration
- `.env.example`: Example environment variables file
- `Pipfile` and `Pipfile.lock`: Dependency management files

## License

[Your License Here]
