# SpeedTest Monitor

A GUI application for running and monitoring internet speed tests over time. This tool allows you to select preferred test servers, schedule regular tests, and save results in various formats for analysis.

![Speed Test Monitor](https://via.placeholder.com/800x400?text=Speed+Test+Monitor+Screenshot)

## ✨ Features

- **Server Selection**: Choose from a list of global speedtest servers or enter a specific server ID
- **Search and Filter**: Search for servers by name or filter by country
- **Scheduled Testing**: Configure automatic speed tests at custom intervals
- **Multiple Output Formats**: Save results in CSV and/or JSON formats for easy data analysis
- **Real-time Visualization**: View your speed test results in real-time charts
- **Error Handling**: Robust error handling with retry mechanisms
- **Logging**: Comprehensive logging for troubleshooting

## 📋 Installation

### Prerequisites

- Python 3.6 or higher
- Tkinter (usually comes with Python)

### Dependencies

```bash
pip install speedtest-cli schedule matplotlib pandas
```

## 🚀 Running the Application

Clone the repository and run the main script:

```bash
git clone https://github.com/rmannby/SpeedTest.git
cd SpeedTest
python speedtest_gui.py
```

## 📊 Usage

### Select a Server:

- Browse through the server list dropdown
- Use the search box to find specific servers
- Filter servers by country using the country dropdown
- Alternatively, enter a specific server ID manually

### Configure Test Settings:

- Set the test interval in minutes
- Select output format(s) (CSV, JSON, or both)

### Start Monitoring:

- Click "Start Speed Test Monitor" to begin the scheduled tests
- The application will display real-time charts of your connection speed
- Results are saved automatically according to your format preferences

## ⚙️ Configuration Options

- **Test Interval**: Set how frequently (in minutes) speed tests should run
- **Output Formats**:
  - CSV: Comma-separated values file for easy spreadsheet import
  - JSON: Structured data format for programmatic analysis

## 📄 Output Data

The application saves test results in your selected format(s) with the following data:

| Data | Description |
|------|-------------|
| Download speed | Measured in Mbps |
| Upload speed | Measured in Mbps |
| Ping/latency | Measured in ms |
| Server information | Host, name, country, and sponsor |
| Timestamp | Date and time of test |

## 📁 File Structure

- `data/` - Directory containing saved test results
  - `speed_test_results.csv` - CSV format results
  - `speed_test_results.json` - JSON format results
- `logs/` - Contains application logs
  - `speedtest_gui.log` - GUI application logs
  - `speedtest.log` - Speed test monitor logs

## 🛠️ Troubleshooting

Logs are stored in the `logs/` directory, which can be helpful for troubleshooting any issues.

## 📝 License

[MIT License](LICENSE)
