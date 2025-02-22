import tkinter as tk
from tkinter import ttk, messagebox
import speedtest
import threading
from typing import Dict, Tuple
import logging
import time
from speedtest_monitor import SpeedTestMonitor

class SpeedTestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Speed Test Monitor")
        self.root.geometry("600x400")
        
        # Variables
        self.server_var = tk.StringVar()
        self.interval_var = tk.StringVar(value="10")
        self.manual_server_var = tk.StringVar()
        self.servers_dict = {}
        self.loading = False
        self.retry_count = 0
        self.max_retries = 3
        
        # Create GUI elements
        self.create_widgets()
        
        # Start server list loading
        self.load_servers()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Server selection
        ttk.Label(main_frame, text="Speed Test Server:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.server_combo = ttk.Combobox(main_frame, textvariable=self.server_var, state="readonly", width=50)
        self.server_combo.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.server_combo["values"] = ["Loading servers..."]
        self.server_combo.current(0)
        
        # Manual server entry
        manual_frame = ttk.LabelFrame(main_frame, text="Manual Server ID", padding="5")
        manual_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(manual_frame, text="Server ID:").grid(row=0, column=0, padx=5)
        self.manual_entry = ttk.Entry(manual_frame, textvariable=self.manual_server_var, width=10)
        self.manual_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(manual_frame, text="(e.g., 38854 for PVDataNet Stockholm)").grid(row=0, column=2, padx=5)
        
        # Retry button
        self.retry_button = ttk.Button(manual_frame, text="Retry Server List", command=self.retry_load_servers)
        self.retry_button.grid(row=0, column=3, padx=5)
        
        # Interval selection
        ttk.Label(main_frame, text="Test Interval (minutes):").grid(row=3, column=0, sticky=tk.W, pady=5)
        interval_frame = ttk.Frame(main_frame)
        interval_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        intervals = ["1", "5", "10", "15", "30", "60"]
        for i, interval in enumerate(intervals):
            ttk.Radiobutton(interval_frame, text=interval, value=interval, 
                          variable=self.interval_var).grid(row=0, column=i, padx=10)
        
        # Server info display
        self.server_info = tk.Text(main_frame, height=6, width=50, wrap=tk.WORD)
        self.server_info.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        self.server_info.insert("1.0", "Loading server information...")
        self.server_info.config(state="disabled")
        
        # Start button
        self.start_button = ttk.Button(main_frame, text="Start Speed Test Monitor", 
                                     command=self.start_monitor)
        self.start_button.grid(row=6, column=0, columnspan=2, pady=20)
        
        # Progress indicator
        self.progress = ttk.Progressbar(main_frame, mode="indeterminate")
        self.progress.grid(row=7, column=0, columnspan=2, sticky=(tk.W, tk.E))

    def retry_load_servers(self):
        """Retry loading the server list"""
        self.retry_count = 0
        self.load_servers()

    def load_servers(self):
        """Load speedtest servers in a separate thread"""
        self.loading = True
        self.progress.start()
        self.server_combo.set("Loading servers...")
        self.start_button.state(["disabled"])
        
        thread = threading.Thread(target=self._load_servers_thread)
        thread.daemon = True
        thread.start()

    def _load_servers_thread(self):
        """Thread function for loading servers"""
        try:
            st = speedtest.Speedtest()
            servers = st.get_servers()
            
            # Process servers
            server_list = []
            for server_group in servers.values():
                for server in server_group:
                    server_id = server['id']
                    server_name = f"{server['name']} ({server['country']}) - {server['sponsor']}"
                    server_list.append((server_name, server_id, server))
                    self.servers_dict[server_name] = server
            
            # Sort by name
            server_list.sort(key=lambda x: x[0])
            
            # Update GUI in main thread
            self.root.after(0, self.update_server_list, [s[0] for s in server_list])
            
        except Exception as e:
            if self.retry_count < self.max_retries:
                self.retry_count += 1
                time.sleep(2)  # Wait before retry
                self._load_servers_thread()
            else:
                self.root.after(0, self.handle_server_load_error, str(e))
        finally:
            self.loading = False
            self.root.after(0, self.progress.stop)

    def handle_server_load_error(self, error_msg):
        """Handle server loading error"""
        self.server_combo["values"] = ["Server list unavailable - Use manual server ID"]
        self.server_combo.current(0)
        self.server_info.config(state="normal")
        self.server_info.delete("1.0", tk.END)
        self.server_info.insert("1.0", f"Error loading servers: {error_msg}\n\n"
                              "You can still use the speed test monitor by entering a known server ID manually.")
        self.server_info.config(state="disabled")
        self.start_button.state(["!disabled"])
        messagebox.showwarning("Server List Error", 
                             "Could not load server list. You can still use the monitor by entering "
                             "a server ID manually.\n\nCommon servers:\n"
                             "38854 - PVDataNet Stockholm\n"
                             "28910 - Telia Stockholm")

    def update_server_list(self, server_names):
        """Update the server combo box with the loaded server list"""
        self.server_combo["values"] = server_names
        self.server_combo.current(0)
        self.start_button.state(["!disabled"])
        self.update_server_info()
        
        # Bind the server selection change event
        self.server_combo.bind("<<ComboboxSelected>>", lambda e: self.update_server_info())

    def update_server_info(self):
        """Update the server information display"""
        selected_server = self.server_var.get()
        if selected_server in self.servers_dict:
            server = self.servers_dict[selected_server]
            info = (f"Server: {server['name']}\n"
                   f"Country: {server['country']}\n"
                   f"Sponsor: {server['sponsor']}\n"
                   f"Host: {server['host']}\n"
                   f"Distance: {server['d']:.2f} km")
        else:
            info = "Using manual server ID" if self.manual_server_var.get() else "Server information not available"
            
        self.server_info.config(state="normal")
        self.server_info.delete("1.0", tk.END)
        self.server_info.insert("1.0", info)
        self.server_info.config(state="disabled")

    def start_monitor(self):
        """Start the speed test monitor"""
        try:
            # Check for manual server ID first
            server_id = None
            if self.manual_server_var.get():
                try:
                    server_id = int(self.manual_server_var.get())
                except ValueError:
                    messagebox.showerror("Error", "Invalid server ID. Please enter a valid number.")
                    return
            else:
                # Get server ID from dropdown
                selected_server = self.server_var.get()
                if selected_server in self.servers_dict:
                    server_id = self.servers_dict[selected_server]['id']
                else:
                    messagebox.showerror("Error", "Please select a server or enter a manual server ID.")
                    return
            
            interval = int(self.interval_var.get())
            
            # Hide the configuration window
            self.root.withdraw()
            
            # Start the monitor
            monitor = SpeedTestMonitor(server_id=server_id, interval_minutes=interval)
            monitor.start()
            
            # Show the configuration window again when monitor closes
            self.root.deiconify()
            
        except Exception as e:
            self.show_error(f"Error starting monitor: {str(e)}")

    def show_error(self, message):
        """Show error message"""
        messagebox.showerror("Error", message)

def main():
    root = tk.Tk()
    app = SpeedTestGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()