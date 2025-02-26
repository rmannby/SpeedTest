# speedtest_gui.py
import sys
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from typing import Dict, Tuple
import speedtest
import logging
from pathlib import Path


class SpeedTestGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("SpeedTest Monitor Configuration")
        self.root.geometry("500x400")

        # Set up logging
        self.setup_logging()

        # Variables
        self.server_var = tk.StringVar()
        self.manual_server_var = tk.StringVar()
        self.interval_var = tk.StringVar(value="10")  # Default 10 minutes
        self.search_var = tk.StringVar()
        self.country_var = tk.StringVar()

        # Output format variables
        self.output_format_vars = {
            "csv": tk.BooleanVar(value=True),
            "json": tk.BooleanVar(value=False),
        }

        # Server loading state
        self.servers_dict = {}
        self.all_servers = []
        self.loading = False
        self.retry_count = 0
        self.max_retries = 3

        self.create_widgets()
        self.load_servers()

    def setup_logging(self):
        """Set up logging configuration"""
        try:
            Path("logs").mkdir(exist_ok=True)
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(levelname)s - %(message)s",
                handlers=[
                    logging.FileHandler("logs/speedtest_gui.log"),
                    logging.StreamHandler(sys.stdout),
                ],
            )
        except Exception as e:
            print(f"Error setting up logging: {str(e)}")

    def create_widgets(self):
        """Create GUI widgets with output format selection"""
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Server selection section
        server_frame = ttk.LabelFrame(main_frame, text="Server Selection", padding="5")
        server_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        # Server list header with refresh button
        server_header = ttk.Frame(server_frame)
        server_header.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))

        ttk.Label(server_header, text="Server List:").pack(side=tk.LEFT)
        self.refresh_button = ttk.Button(
            server_header, text="Refresh Servers", command=self.refresh_servers
        )
        self.refresh_button.pack(side=tk.RIGHT)

        # Search field
        ttk.Label(server_frame, text="Search:").grid(row=1, column=0, sticky=tk.W)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(server_frame, textvariable=self.search_var)
        self.search_entry.grid(row=1, column=1, sticky=(tk.W, tk.E))
        self.search_entry.bind("<KeyRelease>", self.filter_servers)

        # Server selection
        ttk.Label(server_frame, text="Select Server:").grid(
            row=2, column=0, sticky=tk.W
        )
        self.server_dropdown = ttk.Combobox(
            server_frame, textvariable=self.server_var, state="readonly"
        )
        self.server_dropdown.grid(row=2, column=1, sticky=(tk.W, tk.E))

        # Country filter
        ttk.Label(server_frame, text="Filter by Country:").grid(
            row=3, column=0, sticky=tk.W
        )
        self.country_var = tk.StringVar()
        self.country_dropdown = ttk.Combobox(
            server_frame, textvariable=self.country_var, state="readonly"
        )
        self.country_dropdown.grid(row=3, column=1, sticky=(tk.W, tk.E))
        self.country_dropdown.bind("<<ComboboxSelected>>", self.filter_by_country)

        # Manual server entry
        ttk.Label(main_frame, text="Or Enter Server ID:").grid(
            row=1, column=0, sticky=tk.W
        )
        ttk.Entry(main_frame, textvariable=self.manual_server_var).grid(
            row=1, column=1, sticky=(tk.W, tk.E)
        )

        # Test interval
        ttk.Label(main_frame, text="Test Interval (minutes):").grid(
            row=2, column=0, sticky=tk.W
        )
        ttk.Entry(main_frame, textvariable=self.interval_var).grid(
            row=2, column=1, sticky=(tk.W, tk.E)
        )

        # Output format selection
        format_frame = ttk.LabelFrame(main_frame, text="Output Formats", padding="5")
        format_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Checkbutton(
            format_frame, text="CSV", variable=self.output_format_vars["csv"]
        ).grid(row=0, column=0, padx=20)
        ttk.Checkbutton(
            format_frame, text="JSON", variable=self.output_format_vars["json"]
        ).grid(row=0, column=1, padx=20)

        # Start button
        self.start_button = ttk.Button(
            main_frame, text="Start Speed Test Monitor", command=self.start_monitor
        )
        self.start_button.grid(row=7, column=0, columnspan=2, pady=20)

        # Progress indicator
        self.progress = ttk.Progressbar(main_frame, mode="indeterminate")
        self.progress.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E))

    def filter_servers(self, event=None):
        """Filter servers based on search text"""
        search_text = self.search_var.get().lower()
        if not hasattr(self, "all_servers"):
            self.all_servers = list(self.servers_dict.keys())

        filtered_servers = [
            server for server in self.all_servers if search_text in server.lower()
        ]

        self.server_dropdown["values"] = filtered_servers
        if filtered_servers:
            self.server_var.set(filtered_servers[0])

    def filter_by_country(self, event=None):
        """Filter servers by selected country"""
        selected_country = self.country_var.get()

        if selected_country == "All Countries":
            self.server_dropdown["values"] = self.all_servers
        else:
            filtered_servers = [
                server
                for server in self.all_servers
                if f"({selected_country})" in server
            ]
            self.server_dropdown["values"] = filtered_servers

        if self.server_dropdown["values"]:
            self.server_var.set(self.server_dropdown["values"][0])

    def refresh_servers(self):
        """Manually refresh the server list"""
        if not self.loading:
            self.retry_count = 0
            self.refresh_button.config(state="disabled")
            self.load_servers()
            self.root.after(2000, lambda: self.refresh_button.config(state="normal"))

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

                # Store all servers for filtering
                self.all_servers = sorted(self.servers_dict.keys())

                # Update server dropdown
                self.server_var.set(self.all_servers[0] if self.all_servers else "")
                self.server_dropdown["values"] = self.all_servers

                # Extract unique countries for country filter
                countries = sorted(
                    set(
                        server["country"]
                        for server_list in servers.values()
                        for server in server_list
                    )
                )
                country_options = ["All Countries"] + countries
                self.country_dropdown["values"] = country_options
                self.country_var.set("All Countries")

                logging.info(f"Successfully loaded {len(self.all_servers)} servers")
                messagebox.showinfo(
                    "Server List Updated",
                    f"Successfully loaded {len(self.all_servers)} servers",
                )

            except Exception as e:
                if self.retry_count < self.max_retries:
                    self.retry_count += 1
                    logging.warning(
                        f"Retry {self.retry_count}: Failed to load servers - {str(e)}"
                    )
                    self.root.after(5000, _load)  # Retry after 5 seconds
                else:
                    logging.error(
                        f"Failed to load servers after {self.max_retries} attempts: {str(e)}"
                    )
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
            output_formats = [
                fmt for fmt, var in self.output_format_vars.items() if var.get()
            ]
            if not output_formats:
                messagebox.showerror(
                    "Error", "Please select at least one output format."
                )
                return

            # Get server ID
            server_id = None
            if self.manual_server_var.get():
                try:
                    server_id = int(self.manual_server_var.get())
                except ValueError:
                    messagebox.showerror(
                        "Error", "Invalid server ID. Please enter a valid number."
                    )
                    return
            else:
                selected_server = self.server_var.get()
                if selected_server in self.servers_dict:
                    server_id = self.servers_dict[selected_server]["id"]
                else:
                    messagebox.showerror(
                        "Error", "Please select a server or enter a manual server ID."
                    )
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
                    output_formats=output_formats,
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
