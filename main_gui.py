# GUI with GoPro Video Collection and Directory Picker
from Go2Rep.tools.gopro_settings import apply_settings_to_gopro_devices
from Go2Rep.tools.Establish_Wifis import main as Establish_Wifis_GP11
from Go2Rep.tools.Scan_for_GoPros import main as Scan_for_GoPros
from Go2Rep.tools.gopro_capture_GP13 import start_gopro13_capture, stop_gopro13_capture
from Go2Rep.tools.gopro_capture import discover_and_initialize_gopros, start_all, stop_all, disconnect_all
from Go2Rep.tools.Establish_Wifis_GP13 import run_provisioning_gui
from Go2Rep.tools.gopro_video_collector import gopro_video_collection_main
from Go2Rep.tools.gopro_video_collector_GP13 import main as gopro13_video_download_main
from Go2Rep.tools.manual_synchronizer import run_manual_synchronization
from Go2Rep.tools.Theia_classifier import run_theia_classification
from Go2Rep.tools.calib_scene import run_calibration
from Go2Rep.tools.preview_stream import preview_gopro_stream
from Go2Rep.tools.report_generator import generate_report
from Go2Rep.tools.power_off_gopros import power_off_all_gopros_gui
from Go2Rep.tools.timecode_synchronizer import timecode_synchronizer
from Go2Rep.tools.gopro_settings_GP13 import run_gopro13_configuration
import sys
import asyncio
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import nest_asyncio
import threading
import logging
# from open_gopro.logger import setup_logging
import os
import pathlib
import datetime
import webbrowser
from pathlib import Path
from datetime import datetime
from tkcalendar import DateEntry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


nest_asyncio.apply()

def create_time_selector(frame, label_text, var, default):
    subframe = tk.Frame(frame)
    subframe.pack(fill="x", padx=5, pady=2)
    tk.Label(subframe, text=label_text).pack(anchor="w")

    time_frame = tk.Frame(subframe)
    time_frame.pack()

    default_hour, default_minute = default.split(":")
    
    hour_var = tk.StringVar()
    minute_var = tk.StringVar()

    var.set(default)

    def update_time(*args):
        h = hour_var.get().zfill(2)
        m = minute_var.get().zfill(2)
        var.set(f"{h}:{m}")

    hour_spin = tk.Spinbox(time_frame, from_=0, to=23, wrap=True, width=3, state="readonly",
                           textvariable=hour_var, format="%02.0f", command=update_time)
    hour_spin.pack(side="left")

    tk.Label(time_frame, text=":").pack(side="left")

    minute_spin = tk.Spinbox(time_frame, from_=0, to=59, wrap=True, width=3, state="readonly",
                             textvariable=minute_var, format="%02.0f", command=update_time)
    minute_spin.pack(side="left")

    hour_var.set(default_hour)
    minute_var.set(default_minute)

    hour_var.trace_add("write", update_time)
    minute_var.trace_add("write", update_time)

    return hour_var, minute_var, var
    
    
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)              
        nest_asyncio.apply()
        self.loop = asyncio.get_event_loop()

    def show_tip(self, event=None):
        if self.tip_window or not self.text:
            return
        x, y, _cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hide_tip(self, event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

class GoProControllerGUI:
    def __init__(self, root, loop):
        self.root = root
        self.loop = loop
        self.root.title("Go2Rep")
        # self.root.geometry("2500x1200")
        self.ble_clients = []
        self.preview_task = None
        self.stop_event = None
        main_frame = tk.Frame(root)
        main_frame.pack(fill="both", expand=True)               
        left_frame = tk.Frame(main_frame, bg="white")
        left_frame.grid(row=0, column=0, sticky="nsew")
        right_frame = tk.Frame(main_frame, bg="#f0f0f0", width=200)
        right_frame.grid(row=0, column=2, sticky="nsew")        
        center_frame = tk.Frame(main_frame, bg="black")  # for preview stream
        center_frame.grid(row=0, column=1, sticky="nsew")        
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=8)
        main_frame.columnconfigure(2, weight=3)
        main_frame.rowconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        center_frame.rowconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
      
        # main_frame.rowconfigure(0, weight=1)
        self.video_label = tk.Label(center_frame, bg="black")
        self.video_label.pack(expand=True, fill="both")    
      
        # --- Directory Picker at Top ---
        self.video_folder_path = tk.StringVar()
        dir_frame = ttk.LabelFrame(left_frame, text="Video Storage Directory")
        dir_frame.pack(fill="x", padx=5, pady=5)
        self.dir_entry = ttk.Entry(dir_frame, textvariable=self.video_folder_path, width=30)
        self.dir_entry.pack(side="left", padx=5, pady=5)
        ttk.Button(dir_frame, text="Browse", command=self.browse_folder).pack(side="left", padx=5)        
       
        # --- Theia Classified Directory Picker ---
        theia_frame = ttk.LabelFrame(left_frame, text="Theia Classified Directory")
        theia_frame.pack(fill="x", padx=10, pady=5)
        self.theia_folder_path = tk.StringVar()
        self.theia_entry = ttk.Entry(theia_frame, textvariable=self.theia_folder_path, width=30)
        self.theia_entry.pack(side="left", padx=5, pady=5)
        ttk.Button(theia_frame, text="Browse", command=self.browse_theia_folder).pack(side="left", padx=5)
       
        # --- Media Date Section ---
        media_date_frame = ttk.LabelFrame(left_frame, text="Media Date Selection")
        media_date_frame.pack(fill="x", padx=10, pady=5)
        
        
        # Default: today
        today = datetime.today()
        self.media_date = tk.StringVar(value=today.strftime("%Y-%m-%d"))
        
        tk.Label(media_date_frame, text="Date:").pack(anchor="w", padx=5)
        self.date_entry = DateEntry(media_date_frame, textvariable=self.media_date, date_pattern='dd-mm-y')
        self.date_entry.set_date(today)
        self.date_entry.pack(fill="x", padx=5, pady=2)              
               
        self.start_time = tk.StringVar(value="00:00")
        self.end_time = tk.StringVar(value="23:59")        
        self.start_hour_var, self.start_minute_var, self.start_time = create_time_selector(media_date_frame, "Start Time:", tk.StringVar(), "00:00")
        self.end_hour_var, self.end_minute_var, self.end_time = create_time_selector(media_date_frame, "End Time:", tk.StringVar(), "23:59")     
        
        # --- Filename Convention Section ---
        filename_frame = ttk.LabelFrame(left_frame, text="Filename Convention")
        filename_frame.pack(fill="x", padx=10, pady=5)
        
        self.filename_convention_var = tk.StringVar(value="[yyyymmdd]_[HHMMSS]-GoPro1234-")
        
        ttk.Label(filename_frame, text="Select naming format:").pack(anchor="w", padx=5, pady=(2, 0))
        
        self.filename_convention_combo = ttk.Combobox(
            filename_frame,
            textvariable=self.filename_convention_var,
            values=[
                "[yyyymmdd]_[HHMMSS]-GoPro1234-",
                "[yyyymmdd]_[HHMMSS]-CAMERA01- (requires QR scan + Download only with AP)"
            ],
            state="readonly"
        )
        self.filename_convention_combo.pack(fill="x", padx=5, pady=5)
        
        # --- GoPro Devices List --- 
        gopro_list_frame = ttk.LabelFrame(left_frame, text="Discovered GoPros", width=10)
        gopro_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # self.gopro_listbox = tk.Listbox(gopro_list_frame, height=6, selectmode="browse")
        # self.gopro_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        
        columns = ("id", "wifi", "password", "selected")
        self.gopro_tree = ttk.Treeview(gopro_list_frame, columns=columns, show="headings", selectmode="browse")
        self.gopro_tree.heading("id", text="GoPro ID")
        self.gopro_tree.heading("wifi", text="WiFi")
        self.gopro_tree.heading("password", text="Password")
        self.gopro_tree.heading("selected", text="Select")       
        self.gopro_tree.column("id", width=100)
        self.gopro_tree.column("wifi", width=100)
        self.gopro_tree.column("password", width=100)
        self.gopro_tree.column("selected", width=60, anchor="center")
        self.gopro_tree.pack(fill="both", expand=True, padx=5, pady=5)
        self.gopro_tree.bind("<Button-1>", self.toggle_checkbox)
        
        
        
        # Create a frame for monocam buttons
        btn_frame = tk.Frame(gopro_list_frame)
        btn_frame.pack(pady=5)
        
        # --- Monocam Operations Frame ---
        monocam_frame = ttk.LabelFrame(gopro_list_frame, text="Monocam Operations")
        monocam_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        # Row 1: Start / Stop / Download buttons
        monocam_btn_frame = tk.Frame(monocam_frame)
        monocam_btn_frame.pack(pady=5)
        
        start_mono_btn = tk.Button(monocam_btn_frame, text="Start", bg="green", fg="white", command=self.on_start_capture_mono)
        start_mono_btn.pack(side="left", padx=5)
        
        stop_mono_btn = tk.Button(monocam_btn_frame, text="Stop", bg="red", fg="white", command=self.on_stop_capture_mono)
        stop_mono_btn.pack(side="left", padx=5)
        
        download_mono_btn = tk.Button(monocam_btn_frame, text="Download", bg="blue", fg="white", command=self.on_collect_videos_mono)
        download_mono_btn.pack(side="left", padx=5)
        
        # Row 2: Preview / Stop Preview buttons
        preview_btn_frame = tk.Frame(monocam_frame)
        preview_btn_frame.pack(pady=(0, 5))
        
        preview_btn = tk.Button(preview_btn_frame, text="Preview Selected GoPro", command=self.preview_selected_gopro, bg="#4a90e2", fg="white", relief="raised")
        preview_btn.pack(side="left", padx=5)
        
        stop_preview_btn = tk.Button(preview_btn_frame, text="Stop Preview", command=self.stop_preview, bg="#5c5c5c", fg="white", relief="raised")
        stop_preview_btn.pack(side="left", padx=5)
        
        # --- Useful Info Frame ---
        useful_info_frame = ttk.LabelFrame(gopro_list_frame, text="Useful Info")
        useful_info_frame.pack(fill="x", padx=5, pady=(5, 10))
        
        help_btn = ttk.Button(useful_info_frame, text="ℹ️Help ", command=self.show_help_popup)
        help_btn.pack(anchor="center", pady=10)
            
        # --- GoPro Model Selector ---
        model_frame = ttk.LabelFrame(right_frame, text="Select GoPro Model")
        model_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        self.gopro_model_var = tk.StringVar(value="GoPro 11")
        self.model_selector = ttk.Combobox(model_frame, textvariable=self.gopro_model_var,
                                      values=["GoPro 11", "GoPro 13"], state="readonly")
        self.model_selector.pack(fill="x", padx=5, pady=5)
        self.model_selector.bind("<<ComboboxSelected>>", self.on_model_change)
                        
        # --- GoPro Tool Section Container ---
        tools_frame = tk.LabelFrame(right_frame, text="GoPro Tools", bg="white", fg="black", highlightbackground="#add8e6", highlightthickness=2, bd=2)
        tools_frame.pack(fill="x", padx=10, pady=10)
                
        # --- Location System Frame ---
        location_frame = ttk.LabelFrame(tools_frame, text="Locate System")
        location_frame.pack(fill="x", padx=5, pady=5)

        button_row = tk.Frame(location_frame)
        button_row.pack(pady=10)
        
        ttk.Button(button_row, text="Scan for GoPros", command=self.on_scan).pack(side="left", padx=5)
        ttk.Button(button_row, text="Establish Wifi connections", command=self.on_establish_wifi).pack(side="left", padx=5)
        ttk.Button(button_row, text="Power Off All GoPros", command=self.on_power_off_gopros).pack(side="left", padx=5)

        # --- Settings Frame ---
        settings_frame = ttk.LabelFrame(tools_frame, text="Settings")
        settings_frame.pack(fill="x", padx=5, pady=5)

        self.fps_var = tk.StringVar()
        self.res_var = tk.StringVar()

        row_frame = tk.Frame(settings_frame)
        row_frame.pack(padx=5, pady=5)
        row_frame.grid_columnconfigure(0, weight=1)
        row_frame.grid_columnconfigure(4, weight=1)

        ttk.Label(row_frame, text="FPS:").grid(row=0, column=1, padx=5)
        self.fps_menu = ttk.Combobox(row_frame, textvariable=self.fps_var, values=["60", "120", "240","GP13-30","GP13-24"], width=5, state="readonly")
        self.fps_menu.grid(row=0, column=2, padx=5)

        ttk.Label(row_frame, text="Res:").grid(row=0, column=3, padx=5)
        self.res_menu = ttk.Combobox(row_frame, textvariable=self.res_var, values=["1080", "2700", "4000","GP13-720p,400","GP13-900p,360"], width=6, state="readonly")
        self.res_menu.grid(row=0, column=4, padx=5)

        ttk.Button(row_frame, text="Apply", command=self.on_apply).grid(row=0, column=5, padx=5)

        # --- Bluetooth Capture Frame ---
        bluetooth_frame = ttk.LabelFrame(tools_frame, text="Bluetooth/WIFI Capture")
        bluetooth_frame.pack(fill="x", padx=5, pady=5)

        button_center_frame = tk.Frame(bluetooth_frame)
        button_center_frame.pack(anchor="center", pady=5)

        start_btn = tk.Button(button_center_frame, text="Start", bg="green", fg="white", command=self.on_start_capture)
        start_btn.pack(side="left", padx=10)

        stop_btn = tk.Button(button_center_frame, text="Stop", bg="red", fg="white", command=self.on_stop_capture)
        stop_btn.pack(side="left", padx=10)

        # --- GoPro Video Collection ---
        video_frame = ttk.LabelFrame(tools_frame, text="GoPro Video Collection (WIFI: AP ou COHN)")
        video_frame.pack(fill="x", padx=5, pady=5)

        collect_btn = ttk.Button(video_frame, text="Download Videos", command=self.on_collect_videos)
        collect_btn.pack(padx=10, pady=10)
        
        
        # --- Synchronization Frame ---
        sync_frame = ttk.LabelFrame(right_frame, text="Synchronization")
        sync_frame.pack(fill="x", padx=10, pady=10)

        sync_btn_frame = tk.Frame(sync_frame)
        sync_btn_frame.pack(padx=10, pady=10)

        manual_sync_btn = ttk.Button(sync_btn_frame, text="Manual Synchronizer", command=self.on_manual_sync)
        manual_sync_btn.pack(side="left", padx=5)

        timecode_sync_btn = ttk.Button(sync_btn_frame, text="Timecode Synchronizer", command=self.on_timecode_sync)
        timecode_sync_btn.pack(side="left", padx=5)
        
        # --- Classification Frame ---
        classify_frame = ttk.LabelFrame(right_frame, text="Classification")
        classify_frame.pack(fill="x", padx=10, pady=10)
        
        # Format selection
        self.format_var = tk.StringVar(value="mp4")
        self.use_sync_var = tk.StringVar(value="Yes")
        
        combo_row = tk.Frame(classify_frame)
        combo_row.pack(padx=5, pady=5, fill="x")
        
        # Inner frame holds everything and centers it
        inner_row = tk.Frame(combo_row)
        inner_row.pack(anchor="center")
        
        # Format
        ttk.Label(inner_row, text="Format:").pack(side="left", padx=(0, 3))
        self.Video_format = ttk.Combobox(inner_row, textvariable=self.format_var, values=["mp4", "avi", "mov"], state="readonly", width=6)
        self.Video_format.pack(side="left", padx=(0, 10))
        
        # Sync
        ttk.Label(inner_row, text="Sync File:").pack(side="left", padx=(0, 3))
        self.sync_dropdown = ttk.Combobox(inner_row, textvariable=self.use_sync_var, values=["Yes", "No"], state="readonly", width=5)
        self.sync_dropdown.pack(side="left", padx=(0, 5))
        
        # Tooltip icon
        info_icon = ttk.Label(inner_row, text="ℹ️", foreground="blue", cursor="question_arrow")
        info_icon.pack(side="left", padx=(2, 0))
        ToolTip(info_icon, "If 'Yes', a Synch JSON file is required. Otherwise, videos are trimmed to the shortest.")
 
        # Classify Button
        classify_btn = ttk.Button(classify_frame, text="Theia Classifier", command=self.on_theia_classify)
        classify_btn.pack(padx=10, pady=10)
        
        
        # --- Calibration Frame ---
        calibration_frame = ttk.LabelFrame(right_frame, text="Calibration")
        calibration_frame.pack(fill="x", padx=10, pady=10)
        
        # Horizontal layout for button and tooltip
        calib_btn_frame = tk.Frame(calibration_frame)
        calib_btn_frame.pack(padx=10, pady=10)
        
        # Calibration button
        calib_btn = ttk.Button(calib_btn_frame, text="Calib_Scene(Object)", command=self.on_calib_scene)
        calib_btn.pack(side="left")
        
        # Info icon next to the button
        info_icon = ttk.Label(calib_btn_frame, text="ℹ️", foreground="blue", cursor="question_arrow")
        info_icon.pack(side="left", padx=5)
        ToolTip(info_icon, "You can also calibrate via Theia using the Theia chessboard.")

        
        # --- Theia Processing Info Frame ---
        theia_info_frame = ttk.LabelFrame(right_frame, text="Theia Processing")
        theia_info_frame.pack(fill="x", padx=10, pady=10)
        
        label = ttk.Label(theia_info_frame, text="If you have all you need, run Theia3D and process!")
        label.pack(padx=10, pady=10)
        
        # --- Report Generator Frame ---
        report_frame = ttk.LabelFrame(right_frame, text="Report Generator")
        report_frame.pack(fill="x", padx=10, pady=10)

        report_btn = ttk.Button(report_frame, text="Generate Report from Theia Output", command=self.on_generate_report)
        report_btn.pack(padx=10, pady=10)

        
        
    def browse_theia_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            print(f"Selected folder: {folder}")
            # Clear existing text
            self.theia_entry.delete(0, tk.END)
            # Insert new text
            self.theia_entry.insert(0, folder)
            self.theia_folder_path.set(folder)
            print(f"Entry widget value after direct set: {self.theia_entry.get()}")
            print(f"StringVar value (implicitly updated): {self.theia_folder_path.get()}")
            self.root.update_idletasks() # Still good to have
            

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            print(f"Selected folder: {folder}")
            # Clear existing text
            self.dir_entry.delete(0, tk.END)
            # Insert new text
            self.dir_entry.insert(0, folder)
            self.video_folder_path.set(folder)
            print(f"Entry widget value after direct set: {self.dir_entry.get()}")
            print(f"StringVar value (implicitly updated): {self.video_folder_path.get()}")
            self.root.update_idletasks() # Still good to have
  
    def show_help_popup(self): 
        import webbrowser
        import tkinter as tk
    
        def open_url(url):
            webbrowser.open_new(url)
    
        help_window = tk.Toplevel(self.root)
        help_window.title("Help and Useful Info")
        help_window.geometry("500x400")
        help_window.resizable(False, False)
    
        container = tk.Frame(help_window)
        container.pack(fill="both", expand=True, padx=10, pady=10)
    
        # --- Precision Time Control ---
        link1 = tk.Label(container, text="Precision Time Control", fg="blue", cursor="hand2", anchor="w", justify="left")
        link1.pack(anchor="w")
        link1.bind("<Button-1>", lambda e: open_url("https://gopro.github.io/labs/control/precisiontime/"))
    
        # --- Settings Control ---
        link2 = tk.Label(container, text="Settings Control", fg="blue", cursor="hand2", anchor="w", justify="left")
        link2.pack(anchor="w", pady=(5, 0))
        link2.bind("<Button-1>", lambda e: open_url("https://gopro.github.io/labs/control/settings/"))
    
        # --- Mocap Barcode ---
        mocap_label = tk.Label(
            container,
            text="Mocap Barcode:\n  mVr10p30fNcNe0L2w40i8M8sMe0fL0",
            font=("Courier", 9),
            justify="left",
            anchor="w"
        )
        mocap_label.pack(anchor="w", padx=10, pady=(5, 0))
    
        # --- Filename Convention QR Code ---
        link3 = tk.Label(container, text="Filename Convention QR Code", fg="blue", cursor="hand2", anchor="w", justify="left")
        link3.pack(anchor="w", pady=(5, 0))
        link3.bind("<Button-1>", lambda e: open_url("https://gopro.github.io/labs/control/basename/"))
    
        # --- Naming Convention ---
        qr_label = tk.Label(
            container,
            text='Naming Convention:\n  oMBASE="[yyyymmdd]_[HHMMSS]-CAMERA02-"',
            font=("Courier", 9),
            justify="left",
            anchor="w"
        )
        qr_label.pack(anchor="w", padx=10, pady=(0, 10))
    
        # --- Media Browser ---
        link4 = tk.Label(container, text="Media Browser (WiFi-AP)", fg="blue", cursor="hand2", anchor="w", justify="left")
        link4.pack(anchor="w")
        link4.bind("<Button-1>", lambda e: open_url("http://10.5.5.9/videos/DCIM/100GOPRO/"))   
    
    def on_model_change(self, event=None):
        # selected_model = self.gopro_model_var.get()
        selected_model =self.model_selector.get()
        logger.info(f"Switched to {selected_model}")
        # Optionally adjust GUI behavior depending on the model
    
    def on_scan(self):
        async def runner():    
            devices = await Scan_for_GoPros()
            self.discovered_gopros = devices or []
            if self.discovered_gopros:
                self.gopro_tree.delete(*self.gopro_tree.get_children())
                for device in self.discovered_gopros:
                    gopro_id = device if isinstance(device, str) else device.get("id", "Unknown")
                    wifi = ""  # Dummy data or extracted from device
                    password = ""  # Dummy data
                    selected = "✓"
                    self.gopro_tree.insert("", "end", values=(gopro_id, wifi, password, selected))
                device_list_str = "\n".join(self.discovered_gopros)
                messagebox.showinfo("Devices Found", f"The following devices were found:\n{device_list_str}")
            else:
                messagebox.showwarning("No Devices", "No GoPro devices found.")
        asyncio.run_coroutine_threadsafe(runner(), self.loop)

    def on_establish_wifi(self):
        selected_model =self.model_selector.get()
        if selected_model == "GoPro 11":
            # Existing logic for GoPro 11
            async def runner():
                gopro_list=self.get_selected_gopros()
                print("Discovered GoPros in listbox:", gopro_list)    
                if not gopro_list:
                    logger.warning(
                        "The GoPro list is empty.\nIt is recommanded to 'Scan for GoPros' first to update the list."
                    )  
                    
                All_GoPro_Profiles, Failed_GoPros = await Establish_Wifis_GP11(gopro_list)
                # 🔄 Update Treeview rows
                for gopro_id, wifi, password in All_GoPro_Profiles:
                    for row in self.gopro_tree.get_children():
                        values = list(self.gopro_tree.item(row)["values"])
                        if values[0] == gopro_id:
                            values[1] = wifi
                            values[2] = password
                            self.gopro_tree.item(row, values=values)
                # Build a user-friendly string of updated Wi-Fi profiles
                profile_list_str = "\n".join(
                    f"{gopro_id}: WiFi='{wifi}', Password='{password}'"
                    for gopro_id, wifi, password in All_GoPro_Profiles
                )
                Failed_GoPros= "\n".join(Failed_GoPros) if Failed_GoPros else "None"
                # Show confirmation message
                messagebox.showinfo(
                    "Wi-Fi Profile Results",
                    f"Wi-Fi details were successfully established for the following cameras:\n{profile_list_str}\n\n"
                    f"Wi-Fi profile setup failed for the following cameras:\n{Failed_GoPros}"
                )
                
            asyncio.run_coroutine_threadsafe(runner(), self.loop)
    
        elif selected_model == "GoPro 13":
            cert_dir = Path("./certifications")
            async def provision_runner():
                gopro_list=self.get_selected_gopros()
                print("Discovered GoPros in listbox:", gopro_list)    
                if not gopro_list:
                    logger.warning(
                        "The GoPro list is empty.\nIt is recommanded to 'Scan for GoPros' first to update the list."
                    )                                 
                await run_provisioning_gui(cert_dir, gopro_list)
    
            asyncio.run_coroutine_threadsafe(provision_runner(), self.loop)

    def on_apply(self):
        selected_model =self.model_selector.get()
        fps = self.fps_menu.get()
        resolution = self.res_menu.get()
        # Early validation
        if selected_model == "GoPro 11":
            if "GP13" in fps or "GP13" in resolution:
                messagebox.showerror(
                    "Invalid Configuration",
                    "GoPro 11 cannot use FPS or Resolution options labeled 'GP13'.\n"
                    "Please select values that do not include 'GP13'."
                )
                return  # Stop execution if validation fails
        try:
            logger.info(f"Apply button clicked. FPS: {fps}, Res: {resolution}, Model: {selected_model}")
    
            if selected_model == "GoPro 11":
                gopro_list=self.get_selected_gopros()
                print("Discovered GoPros in listbox:", gopro_list)    
                if not gopro_list:
                    logger.warning(
                        "The GoPro list is empty.\nIt is recommanded to 'Scan for GoPros' first to update the list."
                    )  
                fps = int(self.fps_menu.get())
                resolution = int(self.res_menu.get())
                asyncio.run_coroutine_threadsafe(
                    apply_settings_to_gopro_devices(fps, resolution, gopro_list, self.root),
                    self.loop
                )
    
            elif selected_model == "GoPro 13":
                # New logic for GoPro 13
                cert_dir = Path("./certifications")
                asyncio.run_coroutine_threadsafe(
                    run_gopro13_configuration(fps, resolution, cert_dir),
                    self.loop
                )
    
            else:
                messagebox.showwarning("Unsupported Model", f"No apply logic defined for {selected_model}")    
        except ValueError:
            messagebox.showerror("Invalid Input", "Select both FPS and Resolution.")
            
    def on_start_capture(self): 
        selected_model =self.model_selector.get()
        async def runner():
            try:
                if selected_model == "GoPro 13":
                    certs_dir = Path("./certifications")
                    await start_gopro13_capture(certs_dir)
                elif selected_model == "GoPro 11":
                    gopro_list=self.get_selected_gopros()
                    # gopro_list = self.gopro_listbox.get(0, tk.END)
                    print("Discovered GoPros in listbox:", gopro_list)    
                    if not gopro_list:
                        logger.warning(
                            "The GoPro list is empty.\nIt is recommanded to 'Scan for GoPros' first to update the list."
                        )  
                    if not self.ble_clients:
                        self.ble_clients = await discover_and_initialize_gopros(gopro_list) 
                    await start_all(self.ble_clients)  
            except Exception as e:
                logger.error(f"Start capture failed: {e}")
                messagebox.showerror("Error", str(e))   
        # asyncio.create_task(runner())
        asyncio.run_coroutine_threadsafe(runner(), self.loop)
    
    
    def on_stop_capture(self):
        selected_model =self.model_selector.get()
    
        async def runner():
            try:
                if selected_model == "GoPro 13":
                    stop_gopro13_capture()
                elif selected_model == "GoPro 11":
                    if self.ble_clients:
                        await stop_all(self.ble_clients)
                        await disconnect_all(self.ble_clients)
                        self.ble_clients = []
            except Exception as e:
                logger.error(f"Stop capture failed: {e}")
                messagebox.showerror("Error", str(e))
    
        asyncio.run_coroutine_threadsafe(runner(), self.loop)
        
    def on_collect_videos(self):

    
        filename_convention_Selected = self.filename_convention_combo.get()
        #Handle FileName Convention
        if not filename_convention_Selected:
            messagebox.showwarning("Filename Convention Required", "Please select a filename convention before proceeding.")
            return  # or handle accordingly
        #File Name Convention
        if "[yyyymmdd]_[HHMMSS]-GoPro1234-" in filename_convention_Selected:
            filename_convention = 1
        elif "[yyyymmdd]_[HHMMSS]-CAMERA01-" in filename_convention_Selected:
            filename_convention = 2
            
        logger.info(f"FileName Convention: {filename_convention_Selected}")
        
        #Handle Video Storage Dir
        folder = self.dir_entry.get()
        if not folder:
            messagebox.showwarning("Folder Not Set", "Please select a video destination folder first.")
            return
    
        selected_model =self.model_selector.get()
        def run_collector():
            dateFromGui = self.date_entry.get()
            dateFormatted = datetime.strptime(dateFromGui, "%d-%m-%Y")
            date = dateFormatted.strftime("%Y-%m-%d")
            start_hour = self.start_hour_var.get()
            start_minute = self.start_minute_var.get()
            
            end_hour = self.end_hour_var.get()
            end_minute = self.end_minute_var.get()
            
            start_time = f"{start_hour.zfill(2)}:{start_minute.zfill(2)}"
            end_time = f"{end_hour.zfill(2)}:{end_minute.zfill(2)}"
            start=start_time
            end=end_time
            
            time_range = (start, end) if start and end else None
            try:
                if selected_model == "GoPro 13":
                    certs_dir = Path("./certifications")
                    asyncio.run(gopro13_video_download_main(certs_dir,folder))
                    downloaded_GoPros=[]
                else:  # GoPro 11 or default
                    gopro_list=self.get_selected_gopros()
                    print("Discovered GoPros in listbox:", gopro_list)    
                    if not gopro_list:
                        logger.warning(
                            "The GoPro list is empty.\nIt is recommanded to 'Scan for GoPros' first to update the list."
                        )  
                    downloaded_GoPros, empty_GoPros, Failed_GoPros = asyncio.run(gopro_video_collection_main(gopro_list, date, time_range, folder, filename_convention))

                
            except Exception as e:
                logger.error(f"Video collection failed: {e}")
                messagebox.showerror("Collection Failed", str(e))  
            if downloaded_GoPros:
                downloaded_str = "\n".join(downloaded_GoPros)
                empty_str = "\n".join(empty_GoPros) if empty_GoPros else "None"
                Failed_GoPros= "\n".join(Failed_GoPros) if Failed_GoPros else "None"
                messagebox.showinfo(
                    "Success", 
                    f"Videos collected from the following GoPros:\n{downloaded_str}\n\n"
                    f"GoPros with no videos in the selected time range:\n{empty_str}\n\n"
                    f"GoPros with failure to download:\n{Failed_GoPros}\n\n"
                    f"Saved to: {folder}"
                )
            else:
                if selected_model == "GoPro 11":
                    messagebox.showinfo("No Videos", "No videos were downloaded from any GoPros")
    
        threading.Thread(target=run_collector, daemon=True).start()
        
    def on_manual_sync(self):
        video_folder = self.dir_entry.get()
        theia_folder = self.theia_entry.get()
        filename_convention_Selected = self.filename_convention_combo.get()
        #Handle FileName Convention
        if not filename_convention_Selected:
            messagebox.showwarning("Filename Convention Required", "Please select a filename convention before proceeding.")
            return  # or handle accordingly
        #File Name Convention
        if "[yyyymmdd]_[HHMMSS]-GoPro1234-" in filename_convention_Selected:
            filename_convention = 1
        elif "[yyyymmdd]_[HHMMSS]-CAMERA01-" in filename_convention_Selected:
            filename_convention = 2
            
        logger.info(f"FileName Convention: {filename_convention_Selected}")
        
        if not video_folder or not theia_folder :
            messagebox.showwarning("Folder Not Set", "Please select both Video Storage and Theia Classified directories.")
            return

        def run_sync():
            try:
                run_manual_synchronization(video_folder, theia_folder,filename_convention)
                messagebox.showinfo("Sync Complete", f"Synchronization completed.\nCheck logs for details.")
            except Exception as e:
                logger.error(f"Manual synchronization failed: {e}")
                messagebox.showerror("Synchronization Failed", str(e))
        run_sync()        
        # threading.Thread(target=run_sync, daemon=True).start()
        
    def on_timecode_sync(self):
        video_folder = self.dir_entry.get()
        theia_folder = self.theia_entry.get()
        
        filename_convention_Selected = self.filename_convention_combo.get()
        #Handle FileName Convention
        if not filename_convention_Selected:
            messagebox.showwarning("Filename Convention Required", "Please select a filename convention before proceeding.")
            return  # or handle accordingly
        #File Name Convention
        if "[yyyymmdd]_[HHMMSS]-GoPro1234-" in filename_convention_Selected:
            filename_convention = 1
        elif "[yyyymmdd]_[HHMMSS]-CAMERA01-" in filename_convention_Selected:
            filename_convention = 2
            
        logger.info(f"FileName Convention: {filename_convention_Selected}")
        
        if not video_folder or not theia_folder :
            messagebox.showwarning("Folder Not Set", "Please select both Video Storage and Theia Classified directories.")
            return
    
        print(f"🔄 Running timecode synchronization on folder: {video_folder}")
        try:
            timecode_synchronizer(video_folder, theia_folder, filename_convention)
            print("✅ Timecode synchronization complete.")
        except Exception as e:
            print(f"❌ Error during synchronization: {e}")
        
        
    def on_theia_classify(self):
        source_dir = self.dir_entry.get()
        target_dir = self.theia_entry.get()
        use_sync=self.sync_dropdown.get() 
        format_choice =self.Video_format.get()
        if not format_choice or not use_sync :
            messagebox.showwarning("Video format or Synch file use required", "Video format or Synch file use is not selected. Please select them")
            return  # or handle accordingly
        if use_sync=='No': use_sync=False 
        else: use_sync=True
        #Handle FileName Convention*
        filename_convention_Selected = self.filename_convention_combo.get()
        if not filename_convention_Selected:
            messagebox.showwarning("Filename Convention Required", "Please select a filename convention before proceeding.")
            return  # or handle accordingly
        #File Name Convention
        if "[yyyymmdd]_[HHMMSS]-GoPro1234-" in filename_convention_Selected:
            filename_convention = 1
        elif "[yyyymmdd]_[HHMMSS]-CAMERA01-" in filename_convention_Selected:
            filename_convention = 2
            
        logger.info(f"FileName Convention: {filename_convention_Selected}")

        if not source_dir or not target_dir:
            messagebox.showwarning("Folder Not Set", "Please select both Video Storage and Theia Classified directories.")
            return

        def run_classifier():
            try:
                run_theia_classification(source_dir, target_dir, use_sync=use_sync, format_choice=format_choice, filename_convention=filename_convention)
                messagebox.showinfo("Classification Complete", f"Theia classification completed.\nCheck output at: {target_dir}")
            except Exception as e:
                logger.error(f"Theia classification failed: {e}")
                messagebox.showerror("Classification Failed", str(e))

        threading.Thread(target=run_classifier, daemon=True).start()
        
    def on_calib_scene(self):
        source_folder = self.dir_entry.get()
        target_dir = self.theia_entry.get()
        filename_convention_Selected = self.filename_convention_combo.get()
        #Handle FileName Convention
        if not filename_convention_Selected:
            messagebox.showwarning("Filename Convention Required", "Please select a filename convention before proceeding.")
            return  # or handle accordingly
        #File Name Convention
        if "[yyyymmdd]_[HHMMSS]-GoPro1234-" in filename_convention_Selected:
            filename_convention = 1
        elif "[yyyymmdd]_[HHMMSS]-CAMERA01-" in filename_convention_Selected:
            filename_convention = 2
            
        logger.info(f"FileName Convention: {filename_convention_Selected}")
        if not source_folder:
            messagebox.showwarning("Folder Not Set", "Please select a video storage directory first.")
            return

        #VideoExtrisic_destination_root = r"C:\ProgramData\anaconda3\envs\opengopro_env\Lib\site-packages\tutorial_modules\My_Codes\Extrinsic_Calib\Pose2Sim_Folder_Struct\calibration\extrinsics"
        current_dir = pathlib.Path(__file__).resolve().parent  # This gets the directory where main_GUI is located
        project_dir = current_dir / "calib"  # Assuming 'calib' is a subfolder
        VideoExtrisic_destination_root = current_dir / "calib" / "calibration" / "extrinsics"
        # Create Calibration directory if it doesn't exist
        target_calibration_dir = os.path.join(target_dir, "Calibration")
        os.makedirs(target_calibration_dir, exist_ok=True)
        def run_calib_scene():
            try:
                # You could later make index selection GUI-driven
                run_calibration(source_folder, target_calibration_dir, VideoExtrisic_destination_root, project_dir, selected_idx=0, filename_convention=filename_convention)
                messagebox.showinfo("Calibration Complete", f"and saved to: \n {target_calibration_dir}")
            except Exception as e:
                logger.error(f"Calibration failed: {e}")
                messagebox.showerror("Calibration Failed", str(e))

        run_calib_scene()
        
    

    def on_generate_report(self):
        try:
            generate_report()  # No arguments passed
            print("✅ Report generation completed.")
        except Exception as e:
            print(f"❌ Report generation failed: {e}")
        
    def preview_selected_gopro(self):
        selected_item = self.gopro_tree.selection()  # Gets tuple of selected item IDs
        if not selected_item:
            messagebox.showwarning("No GoPro Selected", "Please select a GoPro from the list.")
            return
    
        # Get values of the selected row
        values = self.gopro_tree.item(selected_item[0], "values")
        selected_gopro_id = values[0]  # The GoPro ID (first column)


        # Stop previous preview if any
        if self.stop_event:
            self.stop_event.set()

        self.stop_event = asyncio.Event()

        async def run_preview():
            try:
                await preview_gopro_stream(selected_gopro_id, self.video_label, self.stop_event)
            except Exception as e:
                messagebox.showerror("Preview Error", f"Failed to preview: {str(e)}")

        def start_preview_task():
            asyncio.run(run_preview())

        threading.Thread(target=start_preview_task, daemon=True).start()
        

    def stop_preview(self):
        if self.stop_event:
            self.stop_event.set()

    
    def on_power_off_gopros(self):
        confirm = messagebox.askyesno("Power Off All GoPros", "Are you sure you want to power off all GoPros?")
        if confirm:
            def background_task():
                try:
                    # Pass the global logger instance here
                    # You might also want to pass appropriate values for wired, wifi_interface, log
                    power_off_all_gopros_gui(wired=False, wifi_interface=None, log=True, logger=logger) # PASS logger
                    self.root.after(0, lambda: messagebox.showinfo("Success", "Power off commands sent to all GoPros."))
                except Exception as e:
                    self.root.after(0, lambda e=e: messagebox.showerror("Error", f"Failed to power off GoPros:\n{e}"))
            threading.Thread(target=background_task, daemon=True).start()
    
    
    

    def toggle_checkbox(self, event):
        region = self.gopro_tree.identify_region(event.x, event.y)
        column = self.gopro_tree.identify_column(event.x)
        if column == "#4":  # 4th column is "Selected"
            row_id = self.gopro_tree.identify_row(event.y)
            if row_id:
                current_values = list(self.gopro_tree.item(row_id, "values"))
                current_values[3] = "✓" if current_values[3] == "✗" else "✗"
                self.gopro_tree.item(row_id, values=current_values)

    def get_selected_gopros(self):
        selected = []
        for row in self.gopro_tree.get_children():
            values = self.gopro_tree.item(row)["values"]
            if values[3] == "✓":
                selected.append(values[0])  # Add ID or full data
        return selected

    def on_start_capture_mono(self):
        # selected_model = self.gopro_model_var.get()
        # Get selected GoPro from TreeView
        selected_item = self.gopro_tree.selection()
        if not selected_item:
            messagebox.showwarning("No GoPro Selected", "Please select a GoPro from the list.")
            return
    
        values = self.gopro_tree.item(selected_item[0], "values")
        selected_gopro_id = values[0]  # assuming the first column is GoPro ID
        async def runner():
            try:
                gopro_list=[selected_gopro_id]
                print("Selected Mono GoPro:", gopro_list)    
                if not gopro_list:
                    logger.warning(
                        "The GoPro list is empty.\nIt is recommanded to 'Scan for GoPros' first to update the list."
                    )  
                if not self.ble_clients:
                    self.ble_clients = await discover_and_initialize_gopros(gopro_list) 
                await start_all(self.ble_clients)  
            except Exception as e:
                logger.error(f"Start capture failed: {e}")
                messagebox.showerror("Error", str(e))   
        # asyncio.create_task(runner())
        asyncio.run_coroutine_threadsafe(runner(), self.loop)

    def on_stop_capture_mono(self):
        #selected_model =self.model_selector.get()
    
        async def runner():
            try:
                if self.ble_clients:
                    await stop_all(self.ble_clients)
                    await disconnect_all(self.ble_clients)
                    self.ble_clients = []
            except Exception as e:
                logger.error(f"Stop capture failed: {e}")
                messagebox.showerror("Error", str(e))
    
        asyncio.run_coroutine_threadsafe(runner(), self.loop)
    
    def on_collect_videos_mono(self):
        folder = self.dir_entry.get()
        
        filename_convention_Selected = self.filename_convention_combo.get()
        #Handle FileName Convention
        if not filename_convention_Selected:
            messagebox.showwarning("Filename Convention Required", "Please select a filename convention before proceeding.")
            return  # or handle accordingly
        #File Name Convention
        if "[yyyymmdd]_[HHMMSS]-GoPro1234-" in filename_convention_Selected:
            filename_convention = 1
        elif "[yyyymmdd]_[HHMMSS]-CAMERA01-" in filename_convention_Selected:
            filename_convention = 2
            
        logger.info(f"FileName Convention: {filename_convention_Selected}")
        
        if not folder:
            messagebox.showwarning("Folder Not Set", "Please select a video destination folder first.")
            return
    
        # Get selected GoPro from TreeView
        selected_item = self.gopro_tree.selection()
        if not selected_item:
            messagebox.showwarning("No GoPro Selected", "Please select a GoPro from the list.")
            return
    
        values = self.gopro_tree.item(selected_item[0], "values")
        selected_gopro_id = values[0]  # assuming the first column is GoPro ID
    
        def run_collector():
            try:
                date_from_gui = self.date_entry.get()
                date_formatted = datetime.strptime(date_from_gui, "%d-%m-%Y")
                date = date_formatted.strftime("%Y-%m-%d")
    
                start_hour = self.start_hour_var.get().zfill(2)
                start_minute = self.start_minute_var.get().zfill(2)
                end_hour = self.end_hour_var.get().zfill(2)
                end_minute = self.end_minute_var.get().zfill(2)
    
                start_time = f"{start_hour}:{start_minute}"
                end_time = f"{end_hour}:{end_minute}"
                time_range = (start_time, end_time)
    
                gopro_list = [selected_gopro_id]
                print("Selected Mono GoPro:", gopro_list)
    
                downloaded_GoPros, empty_GoPros, Failed_GoPros = asyncio.run(
                    gopro_video_collection_main(gopro_list, date, time_range, folder, filename_convention)
                )
    
                if downloaded_GoPros:
                    downloaded_str = "\n".join(downloaded_GoPros)
                    empty_str = "\n".join(empty_GoPros) if empty_GoPros else "None"
                    failed_str = "\n".join(Failed_GoPros) if Failed_GoPros else "None"
    
                    messagebox.showinfo(
                        "Success",
                        f"Videos collected from the following GoPro:\n{downloaded_str}\n\n"
                        f"No videos found for the time range:\n{empty_str}\n\n"
                        f"Failed to download:\n{failed_str}\n\n"
                        f"Saved to: {folder}"
                    )
                else:
                    messagebox.showinfo("No Videos", "No videos were downloaded from the selected GoPro.")
    
            except Exception as e:
                logger.error(f"Mono video collection failed: {e}")
                messagebox.showerror("Collection Failed", str(e))
    
        threading.Thread(target=run_collector, daemon=True).start()

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()



if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    threading.Thread(target=start_loop, args=(loop,), daemon=True).start()
    root = tk.Tk()
    app = GoProControllerGUI(root, loop)
    root.mainloop()
