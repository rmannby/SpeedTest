SpeedTest Monitor
A GUI application for running and monitoring internet speed tests over time. This tool allows you to select preferred test servers, schedule regular tests, and save results in various formats for analysis.

Features
Server Selection: Choose from a list of global speedtest servers or enter a specific server ID
Search and Filter: Search for servers by name or filter by country
Scheduled Testing: Configure automatic speed tests at custom intervals
Multiple Output Formats: Save results in CSV and/or JSON formats for easy data analysis
Error Handling: Robust error handling with retry mechanisms
Logging: Comprehensive logging for troubleshooting
Installation
Prerequisites
Python 3.6 or higher
Tkinter (usually comes with Python)
Dependencies
pip install speedtest-cli

Copy

Execute

Running the Application
Clone the repository and run the main script:

git clone https://github.com/rmannby/SpeedTest.git
cd SpeedTest
python speedtest_gui.py

Copy

Execute

Usage
Select a Server:

Browse through the server list dropdown
Use the search box to find specific servers
Filter servers by country using the country dropdown
Alternatively, enter a specific server ID manually
Configure Test Settings:

Set the test interval in minutes
Select output format(s) (CSV, JSON, or both)
Start Monitoring:

Click "Start Speed Test Monitor" to begin the scheduled tests
The application will run in the background according to your settings
Configuration Options
Test Interval: Set how frequently (in minutes) speed tests should run
Output Formats:
CSV: Comma-separated values file for easy spreadsheet import
JSON: Structured data format for programmatic analysis
Output Data
The application saves test results in your selected format(s) with the following data:

Download speed
Upload speed
Ping/latency
Server information
Timestamp
Logs
Logs are stored in the logs/speedtest_gui.log file, which can be helpful for troubleshooting any issues.