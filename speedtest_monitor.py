import speedtest
import schedule
import time
import csv
import json
from datetime import datetime
import logging
import sys
from typing import Optional, Dict, List
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
from collections import deque
import threading
from pathlib import Path

class SpeedTestMonitor:
    def __init__(self, server_id: Optional[int] = None, interval_minutes: int = 10, 
                 output_formats: List[str] = ['csv', 'json']):
        # Create logs directory if it doesn't exist
        Path('logs').mkdir(exist_ok=True)
        
        # Set up logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/speedtest.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.server_id = server_id
        self.interval_minutes = interval_minutes
        self.running = True
        self.output_formats = [fmt.lower() for fmt in output_formats]
        
        # File paths
        self.data_dir = Path('data')
        self.data_dir.mkdir(exist_ok=True)
        self.csv_file = self.data_dir / 'speed_test_results.csv'
        self.json_file = self.data_dir / 'speed_test_results.json'
        
        # Initialize data structures
        self.MAX_POINTS = 50
        self.timestamps = deque(maxlen=self.MAX_POINTS)
        self.download_speeds = deque(maxlen=self.MAX_POINTS)
        self.upload_speeds = deque(maxlen=self.MAX_POINTS)
        self.pings = deque(maxlen=self.MAX_POINTS)
        
        # Ensure output directories exist
        self.initialize_output_files()
        
        # Set up plotting
        plt.style.use('dark_background')
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        self.fig.suptitle('Real-time Internet Speed Test Results')
        
        self.line_download, = self.ax1.plot([], [], label='Download', color='#00ff00', linewidth=2)
        self.line_upload, = self.ax1.plot([], [], label='Upload', color='#00ffff', linewidth=2)
        self.line_ping, = self.ax2.plot([], [], label='Ping', color='#ff9900', linewidth=2)
        
        self.ax1.set_ylabel('Speed (Mbps)')
        self.ax1.grid(True, alpha=0.3)
        self.ax1.legend()
        
        self.ax2.set_ylabel('Ping (ms)')
        self.ax2.set_xlabel('Time')
        self.ax2.grid(True, alpha=0.3)
        self.ax2.legend()
        
        # Load existing data
        self.load_existing_data()
        
        # Create scheduler thread
        self.scheduler_thread = threading.Thread(target=self.run_scheduler)
        self.scheduler_thread.daemon = True

    def initialize_output_files(self):
        """Initialize output files and directories"""
        try:
            # Initialize CSV file
            if 'csv' in self.output_formats and not self.csv_file.exists():
                with open(self.csv_file, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        'Timestamp',
                        'Download (Mbps)',
                        'Upload (Mbps)',
                        'Ping (ms)',
                        'Server Host',
                        'Server Name',
                        'Server Country',
                        'Server Sponsor'
                    ])
            
            # Initialize JSON file
            if 'json' in self.output_formats and not self.json_file.exists():
                with open(self.json_file, 'w') as f:
                    json.dump({'speed_tests': []}, f, indent=2)
                    
        except Exception as e:
            logging.error(f"Error initializing output files: {str(e)}")
            raise

    def run_speed_test(self):
        """Run a single speed test"""
        try:
            logging.info(f"Running scheduled test (Every {self.interval_minutes} minutes)")
            st = speedtest.Speedtest()
            
            # Get servers list first
            servers = st.get_servers()
            
            if self.server_id:
                # Filter for specific server if ID provided
                server = next((s for s in servers for sl in servers.values() 
                             for s in sl if s['id'] == self.server_id), None)
                if not server:
                    raise ValueError(f"Server with ID {self.server_id} not found")
            else:
                # Get best server if no specific ID
                server = st.get_best_server()
                
            logging.info(f"Using server: {server['host']} ({server['name']}, {server['country']}) - {server['sponsor']}")
            
            # Run tests
            download_speed = st.download() / 1_000_000  # Convert to Mbps
            upload_speed = st.upload() / 1_000_000    # Convert to Mbps
            ping = st.results.ping
            
            current_time = datetime.now()
            timestamp = current_time.strftime("%Y-%m-%d %H:%M")
            
            # Update data structures
            self.timestamps.append(current_time)
            self.download_speeds.append(download_speed)
            self.upload_speeds.append(upload_speed)
            self.pings.append(ping)
            
            # Prepare data dictionary
            data = {
                'timestamp': timestamp,
                'download_speed': download_speed,
                'upload_speed': upload_speed,
                'ping': ping,
                'server_host': server['host'],
                'server_name': server['name'],
                'server_country': server['country'],
                'server_sponsor': server['sponsor']
            }
            
            # Save results
            self.save_results(data)
            
            logging.info(f"Speed test completed - Down: {download_speed:.2f} Mbps, Up: {upload_speed:.2f} Mbps, Ping: {ping:.1f} ms")
            return True
            
        except Exception as e:
            logging.error(f"Error running speed test: {str(e)}")
            return False

    def save_results(self, data: Dict):
        """Save results in specified formats"""
        try:
            if 'csv' in self.output_formats:
                self.save_to_csv(data)
            if 'json' in self.output_formats:
                self.save_to_json(data)
        except Exception as e:
            logging.error(f"Error saving results: {str(e)}")

    def save_to_csv(self, data: Dict):
        """Save results to CSV file"""
        try:
            with open(self.csv_file, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    data['timestamp'],
                    data['download_speed'],
                    data['upload_speed'],
                    data['ping'],
                    data['server_host'],
                    data['server_name'],
                    data['server_country'],
                    data['server_sponsor']
                ])
        except Exception as e:
            logging.error(f"Error saving to CSV: {str(e)}")

    def save_to_json(self, data: Dict):
        """Save results to JSON file"""
        try:
            # Read existing data
            if self.json_file.exists():
                with open(self.json_file, 'r') as f:
                    json_data = json.load(f)
            else:
                json_data = {'speed_tests': []}
            
            # Add new data
            json_data['speed_tests'].append({
                'timestamp': data['timestamp'],
                'download_speed': round(data['download_speed'], 2),
                'upload_speed': round(data['upload_speed'], 2),
                'ping': round(data['ping'], 1),
                'server': {
                    'host': data['server_host'],
                    'name': data['server_name'],
                    'country': data['server_country'],
                    'sponsor': data['server_sponsor']
                }
            })
            
            # Write updated data
            with open(self.json_file, 'w') as f:
                json.dump(json_data, f, indent=2)
                
        except Exception as e:
            logging.error(f"Error saving to JSON: {str(e)}")

    def load_existing_data(self):
        """Load existing data with proper error handling"""
        try:
            if self.csv_file.exists():
                df = pd.read_csv(self.csv_file)
                if not df.empty:
                    recent_data = df.tail(self.MAX_POINTS)
                    self.timestamps.extend(pd.to_datetime(recent_data['Timestamp']))
                    self.download_speeds.extend(recent_data['Download (Mbps)'])
                    self.upload_speeds.extend(recent_data['Upload (Mbps)'])
                    self.pings.extend(recent_data['Ping (ms)'])
            else:
                logging.info("No existing CSV data found.")
        except Exception as e:
            logging.error(f"Error loading existing data: {str(e)}")
            # Continue with empty data structures
            pass

    def update_plot(self, frame):
        """Update the plot with new data"""
        try:
            # Update lines data
            x_data = range(len(self.download_speeds))
            self.line_download.set_data(x_data, list(self.download_speeds))
            self.line_upload.set_data(x_data, list(self.upload_speeds))
            self.line_ping.set_data(x_data, list(self.pings))
            
            # Adjust axes limits
            if len(self.download_speeds) > 0:
                self.ax1.set_xlim(0, len(self.download_speeds))
                max_speed = max(max(self.download_speeds), max(self.upload_speeds))
                self.ax1.set_ylim(0, max_speed * 1.1)
                
            if len(self.pings) > 0:
                self.ax2.set_xlim(0, len(self.pings))
                self.ax2.set_ylim(0, max(self.pings) * 1.1)
            
            # Add timestamps as x-axis labels
            if len(self.timestamps) > 0:
                self.ax2.set_xticks(range(len(self.timestamps)))
                self.ax2.set_xticklabels([t.strftime('%H:%M') for t in self.timestamps], rotation=45)
            
            return self.line_download, self.line_upload, self.line_ping
        except Exception as e:
            logging.error(f"Error updating plot: {str(e)}")
            return self.line_download, self.line_upload, self.line_ping

    def run_scheduler(self):
        """Run the scheduler loop"""
        schedule.every(self.interval_minutes).minutes.do(self.run_speed_test)
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def start(self):
        """Start the speed test monitor"""
        try:
            # Start the scheduler thread
            self.scheduler_thread.start()
            
            # Run initial test
            self.run_speed_test()
            
            # Set up animation
            ani = FuncAnimation(
                self.fig,
                self.update_plot,
                interval=1000,
                save_count=self.MAX_POINTS,
                cache_frame_data=False
            )
            
            # Show plot (this will block until window is closed)
            plt.show()
            
        except Exception as e:
            logging.error(f"Error starting monitor: {str(e)}")
        finally:
            # Clean up when plot is closed
            self.running = False
            self.scheduler_thread.join(timeout=1)  # Add timeout to prevent hanging

def main(server_id: Optional[int] = None, interval_minutes: int = 10, 
         output_formats: List[str] = ['csv', 'json']):
    try:
        monitor = SpeedTestMonitor(server_id, interval_minutes, output_formats)
        logging.info(f"Starting speed test scheduler (Interval: {interval_minutes} minutes)")
        monitor.start()
    except Exception as e:
        logging.error(f"Error in main: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()