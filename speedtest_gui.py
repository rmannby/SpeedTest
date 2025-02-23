# speedtest_gui.py
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import speedtest
import threading
from typing import Dict, Tuple
import logging
import time
from pathlib import Path

class SpeedTestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Speed Test Monitor")
        self.root.geometry("600x400")
        
        # Set up logging
        self.setup_logging()
        
        # Variables
        self.server_var = tk.StringVar()
        self.interval_var = tk.StringVar(value="10")
        self.manual_server_var = tk.StringVar()
        self.output_format_vars = {
            'csv': tk.BooleanVar(value=True),
            'json': tk.BooleanVar(value=True)
        }
        self.servers_dict = {}
        self.loading = False
        self.retry_count = 0
        self.max_retries = 3
        
        # Create GUI elements
        self.create_widgets()
        
        # Start server list loading
        self.load_servers()

    def setup_logging(self):
        """Set up logging configuration"""
        try:
            Path('logs').mkdir(exist_ok=True)
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler('logs/speedtest_gui.log'),
                    logging.StreamHandler(sys.stdout)
                ]
            )
        except Exception as e:
            print(f"Error setting up logging: {str(e)}")

    def create_widgets(self):
        """Create GUI widgets with output format selection"""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Server selection
        ttk.Label(main_frame, text="Select Server:").grid(row=0, column=0, sticky=tk.W)
        self.server_dropdown = ttk.Combobox(main_frame, textvariable=self.server_var, state="readonly")
        self.server_dropdown.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Manual server entry
        ttk.Label(main_frame, text="Or Enter Server ID:").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(main_frame, textvariable=self.manual_server_var).grid(row=1, column=1, sticky=(tk.W, tk.E))
        
        # Test interval
        ttk.Label(main_frame, text="Test Interval (minutes):").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(main_frame, textvariable=self.interval_var).grid(row=2, column=1, sticky=(tk.W, tk.E))
        
        # Output format selection
        format_frame = ttk.LabelFrame(main_frame, text="Output Formats", padding="5")
        format_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Checkbutton(format_frame, text="CSV", variable=self.output_format_vars['csv']).grid(
            row=0, column=0, padx=20)
        ttk.Checkbutton(format_frame, text="JSON", variable=self.output_format_vars['json']).grid(
            row=0, column=1, padx=20)
        
        # Start button
        self.start_button = ttk.Button(main_frame, text="Start Speed Test Monitor", 
                                     command=self.start_monitor)
        self.start_button.grid(row=7, column=0, columnspan=2, pady=20)
        
        # Progress indicator
        self.progress = ttk.Progressbar(main_frame, mode="indeterminate")
        self.progress.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E))

    def load_servers(self):
        """Load available speedtest servers"""
        def _load():
            try:
                self.loading = True
                self.progress.start()
                st = speedtest.Speedtest()
                servers = st.get_servers()
                
                # Create a dictionary of server names to server info
                self.servers_dict = {
                    f"{server['name']} ({server['country']})": server 
                    for server_list in servers.values() 
                    for server in server_list
                }
                
                # Update server dropdown
                server_names = sorted(self.servers_dict.keys())
                self.server_var.set(server_names[0] if server_names else '')
                self.server_dropdown['values'] = server_names
                
            except Exception as e:
                if self.retry_count < self.max_retries:
                    self.retry_count += 1
                    logging.warning(f"Retry {self.retry_count}: Failed to load servers - {str(e)}")
                    self.root.after(5000, _load)  # Retry after 5 seconds
                else:
                    logging.error(f"Failed to load servers after {self.max_retries} attempts: {str(e)}")
                    self.show_error(f"Failed to load server list: {str(e)}")
            finally:
                self.loading = False
                self.progress.stop()
        
        # Start loading in a separate thread
        threading.Thread(target=_load, daemon=True).start()

    def start_monitor(self):
        """Start the speed test monitor with selected output formats"""
        try:
            # Get selected output formats
            output_formats = [fmt for fmt, var in self.output_format_vars.items() if var.get()]
            if not output_formats:
                messagebox.showerror("Error", "Please select at least one output format.")
                return
            
            # Get server ID
            server_id = None
            if self.manual_server_var.get():
                try:
                    server_id = int(self.manual_server_var.get())
                except ValueError:
                    messagebox.showerror("Error", "Invalid server ID. Please enter a valid number.")
                    return
            else:
                selected_server = self.server_var.get()
                if selected_server in self.servers_dict:
                    server_id = self.servers_dict[selected_server]['id']
                else:
                    messagebox.showerror("Error", "Please select a server or enter a manual server ID.")
                    return
            
            interval = int(self.interval_var.get())
            
            # Hide the configuration window
            self.root.withdraw()
            
            try:
                # Start the monitor with selected output formats
                from speedtest_monitor import SpeedTestMonitor
                monitor = SpeedTestMonitor(
                    server_id=server_id,
                    interval_minutes=interval,
                    output_formats=output_formats
                )
                monitor.start()
            except Exception as e:
                logging.error(f"Error in monitor: {str(e)}")
                raise
            finally:
                # Show the configuration window again when monitor closes
                self.root.deiconify()
            
        except Exception as e:
            self.show_error(f"Error starting monitor: {str(e)}")
            logging.error(f"Error in start_monitor: {str(e)}")
            self.root.deiconify()

    def show_error(self, message):
        """Show error message"""
        messagebox.showerror("Error", message)

def main():
    root = tk.Tk()
    app = SpeedTestGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()