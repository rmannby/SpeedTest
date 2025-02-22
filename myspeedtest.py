import speedtest
import schedule
import time
import csv
from datetime import datetime
import logging
import sys
from typing import Optional, Dict
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
from collections import deque
import threading

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('speedtest.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

class SpeedTestMonitor:
    def __init__(self, server_id: Optional[int] = 38854, interval_minutes: int = 10):
        self.server_id = server_id
        self.interval_minutes = interval_minutes
        self.running = True
        
        # Initialize data structures
        self.MAX_POINTS = 50
        self.timestamps = deque(maxlen=self.MAX_POINTS)
        self.download_speeds = deque(maxlen=self.MAX_POINTS)
        self.upload_speeds = deque(maxlen=self.MAX_POINTS)
        self.pings = deque(maxlen=self.MAX_POINTS)
        
        # Set up the plot
        plt.style.use('dark_background')
        self.fig, (self.ax1, self.ax2) = plt.subplots(2, 1, figsize=(12, 8))
        self.fig.suptitle('Real-time Internet Speed Test Results')
        
        # Initialize lines
        self.line_download, = self.ax1.plot([], [], label='Download', color='#00ff00', linewidth=2)
        self.line_upload, = self.ax1.plot([], [], label='Upload', color='#00ffff', linewidth=2)
        self.line_ping, = self.ax2.plot([], [], label='Ping', color='#ff9900', linewidth=2)
        
        # Configure axes
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

    def run_speed_test(self):
        try:
            logging.info(f"Running scheduled test (Every {self.interval_minutes} minutes)")
            st = speedtest.Speedtest()
            
            if self.server_id:
                st.get_servers([self.server_id])
                server = st.get_best_server()
            else:
                server = st.get_best_server()
                
            logging.info(f"Using server: {server['host']} ({server['name']}, {server['country']}) - {server['sponsor']}")
            
            download_speed = st.download() / 1_000_000
            upload_speed = st.upload() / 1_000_000
            ping = st.results.ping
            
            current_time = datetime.now()
            timestamp = current_time.strftime("%Y-%m-%d %H:%M")
            
            self.timestamps.append(current_time)
            self.download_speeds.append(download_speed)
            self.upload_speeds.append(upload_speed)
            self.pings.append(ping)
            
            with open('speed_test_results.csv', 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    timestamp,
                    download_speed,
                    upload_speed,
                    ping,
                    server['host'],
                    server['name'],
                    server['country'],
                    server['sponsor']
                ])
            
            logging.info(f"Speed test completed - Down: {download_speed:.2f} Mbps, Up: {upload_speed:.2f} Mbps, Ping: {ping:.1f} ms")
            return True
            
        except Exception as e:
            logging.error(f"Error running speed test: {str(e)}")
            return False

    def update_plot(self, frame):
        # Update lines data
        self.line_download.set_data(range(len(self.download_speeds)), list(self.download_speeds))
        self.line_upload.set_data(range(len(self.upload_speeds)), list(self.upload_speeds))
        self.line_ping.set_data(range(len(self.pings)), list(self.pings))
        
        # Adjust axes limits
        if len(self.download_speeds) > 0:
            self.ax1.set_xlim(0, len(self.download_speeds))
            self.ax1.set_ylim(0, max(max(self.download_speeds), max(self.upload_speeds)) * 1.1)
            
        if len(self.pings) > 0:
            self.ax2.set_xlim(0, len(self.pings))
            self.ax2.set_ylim(0, max(self.pings) * 1.1)
        
        # Add timestamps as x-axis labels
        if len(self.timestamps) > 0:
            self.ax2.set_xticks(range(len(self.timestamps)))
            self.ax2.set_xticklabels([t.strftime('%H:%M') for t in self.timestamps], rotation=45)
        
        return self.line_download, self.line_upload, self.line_ping

    def load_existing_data(self):
        try:
            df = pd.read_csv('speed_test_results.csv')
            if len(df) > 0:
                recent_data = df.tail(self.MAX_POINTS)
                self.timestamps.extend(pd.to_datetime(recent_data['Timestamp']))
                self.download_speeds.extend(recent_data['Download (Mbps)'])
                self.upload_speeds.extend(recent_data['Upload (Mbps)'])
                self.pings.extend(recent_data['Ping (ms)'])
        except FileNotFoundError:
            pass

    def run_scheduler(self):
        schedule.every(self.interval_minutes).minutes.do(self.run_speed_test)
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def start(self):
        # Create CSV file with headers if it doesn't exist
        try:
            with open('speed_test_results.csv', 'x', newline='') as f:
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
        except FileExistsError:
            pass

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
        
        # Clean up when plot is closed
        self.running = False
        self.scheduler_thread.join()

def main(server_id: Optional[int] = 38854, interval_minutes: int = 10):
    monitor = SpeedTestMonitor(server_id, interval_minutes)
    logging.info(f"Starting speed test scheduler (Interval: {interval_minutes} minutes)")
    monitor.start()

if __name__ == "__main__":
    main()