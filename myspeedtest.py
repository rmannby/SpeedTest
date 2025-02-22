import speedtest
import schedule
import time
import csv
from datetime import datetime
import logging
import sys
from typing import Optional, Dict

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('speedtest.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

def get_server_list() -> Dict[int, Dict]:
    """
    Get list of available speedtest servers
    """
    try:
        st = speedtest.Speedtest()
        servers = st.get_servers()
        
        # Create a dictionary of servers with their details
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

def run_speed_test(server_id: Optional[int] = None):
    """
    Run a speed test and return the results
    Args:
        server_id: Optional specific server ID to use for testing
    """
    try:
        logging.info("Starting speed test...")
        st = speedtest.Speedtest()
        
        # Get server info
        if server_id:
            st.get_servers([server_id])
            server = st.get_best_server()
        else:
            server = st.get_best_server()
            
        logging.info(f"Using server: {server['host']} ({server['name']}, {server['country']}) - {server['sponsor']}")
        
        # Run speed test
        download_speed = st.download() / 1_000_000  # Convert to Mbps
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps
        ping = st.results.ping
        
        # Get timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        
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

def main(server_id: Optional[int] = None, interval_minutes: int = 60):
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

    # List available servers
    list_available_servers()
    
    # Set up schedule
    setup_schedule(interval_minutes, server_id)
    
    # Run initial test
    run_speed_test(server_id)
    
    # Keep the script running
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    logging.info("Starting speed test scheduler")
    main()