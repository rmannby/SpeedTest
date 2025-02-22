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

# Global variables for real-time plotting
MAX_POINTS = 50  # Maximum number of points to show on the graph
timestamps = deque(maxlen=MAX_POINTS)
download_speeds = deque(maxlen=MAX_POINTS)
upload_speeds = deque(maxlen=MAX_POINTS)
pings = deque(maxlen=MAX_POINTS)

# Create figure and subplots
plt.style.use('dark_background')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
fig.suptitle('Real-time Internet Speed Test Results')

# Initialize empty lines
line_download, = ax1.plot([], [], label='Download', color='#00ff00', linewidth=2)
line_upload, = ax1.plot([], [], label='Upload', color='#00ffff', linewidth=2)
line_ping, = ax2.plot([], [], label='Ping', color='#ff9900', linewidth=2)

# Configure axes
ax1.set_ylabel('Speed (Mbps)')
ax1.grid(True, alpha=0.3)
ax1.legend()

ax2.set_ylabel('Ping (ms)')
ax2.set_xlabel('Time')
ax2.grid(True, alpha=0.3)
ax2.legend()

def get_server_list() -> Dict[int, Dict]:
    """
    Get list of available speedtest servers
    """
    try:
        st = speedtest.Speedtest()
        servers = st.get_servers()
        
        server_dict = {}
        for server_list in servers.values():
            for server in server_list:
                server_dict[server['id']] = {
                    'host': server['host'],
                    'name': server['name'],
                    'country': server['country'],
                    'sponsor': server['sponsor'],
                    'distance': server['d']
                }
        return server_dict
    except Exception as e:
        logging.error(f"Error getting server list: {str(e)}")
        return {}

def update_plot(frame):
    """
    Update function for the animation
    """
    # Update lines data
    line_download.set_data(range(len(download_speeds)), list(download_speeds))
    line_upload.set_data(range(len(upload_speeds)), list(upload_speeds))
    line_ping.set_data(range(len(pings)), list(pings))
    
    # Adjust axes limits
    if len(download_speeds) > 0:
        ax1.set_xlim(0, len(download_speeds))
        ax1.set_ylim(0, max(max(download_speeds), max(upload_speeds)) * 1.1)
        
    if len(pings) > 0:
        ax2.set_xlim(0, len(pings))
        ax2.set_ylim(0, max(pings) * 1.1)
    
    # Add timestamps as x-axis labels
    if len(timestamps) > 0:
        ax2.set_xticks(range(len(timestamps)))
        ax2.set_xticklabels([t.strftime('%H:%M') for t in timestamps], rotation=45)
    
    return line_download, line_upload, line_ping

def run_speed_test(server_id: Optional[int] = None):
    """
    Run a speed test and return the results
    """
    try:
        logging.info("Starting speed test...")
        st = speedtest.Speedtest()
        
        if server_id:
            st.get_servers([server_id])
            server = st.get_best_server()
        else:
            server = st.get_best_server()
            
        logging.info(f"Using server: {server['host']} ({server['name']}, {server['country']}) - {server['sponsor']}")
        
        # Run speed test
        download_speed = st.download() / 1_000_000
        upload_speed = st.upload() / 1_000_000
        ping = st.results.ping
        
        # Get timestamp
        current_time = datetime.now()
        timestamp = current_time.strftime("%Y-%m-%d %H:%M")
        
        # Update plot data
        timestamps.append(current_time)
        download_speeds.append(download_speed)
        upload_speeds.append(upload_speed)
        pings.append(ping)
        
        # Save results to CSV
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

def setup_schedule(interval_minutes=60, server_id: Optional[int] = None):
    """
    Set up the schedule to run the speed test at specified intervals
    """
    if server_id:
        schedule.every(interval_minutes).minutes.do(run_speed_test, server_id=server_id)
    else:
        schedule.every(interval_minutes).minutes.do(run_speed_test)
    logging.info(f"Scheduled speed tests to run every {interval_minutes} minutes")

def list_available_servers():
    """
    Print list of available servers
    """
    servers = get_server_list()
    logging.info("Available servers:")
    for server_id, server in servers.items():
        logging.info(f"ID: {server_id}")
        logging.info(f"  Host: {server['host']}")
        logging.info(f"  Name: {server['name']}")
        logging.info(f"  Country: {server['country']}")
        logging.info(f"  Sponsor: {server['sponsor']}")
        logging.info(f"  Distance: {server['distance']:.2f} km")
        logging.info("---")

def load_existing_data():
    """
    Load existing data from CSV file into the plotting queues
    """
    try:
        df = pd.read_csv('speed_test_results.csv')
        if len(df) > 0:
            recent_data = df.tail(MAX_POINTS)
            timestamps.extend(pd.to_datetime(recent_data['Timestamp']))
            download_speeds.extend(recent_data['Download (Mbps)'])
            upload_speeds.extend(recent_data['Upload (Mbps)'])
            pings.extend(recent_data['Ping (ms)'])
    except FileNotFoundError:
        pass

def main(server_id: Optional[int] = 38854, interval_minutes: int = 10):
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

    # Load existing data
    load_existing_data()
    
    # List available servers
    list_available_servers()
    
    # Set up schedule
    setup_schedule(interval_minutes, server_id)
    
    # Set up animation
    ani = FuncAnimation(fig, update_plot, interval=1000, blit=True)
    
    # Run initial test in a separate thread
    threading.Thread(target=run_speed_test, args=(server_id,)).start()
    
    # Show plot
    plt.show()
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    logging.info("Starting speed test scheduler")
    main()