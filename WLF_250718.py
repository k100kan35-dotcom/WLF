import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.interpolate import UnivariateSpline
import tkinter as tk
from tkinter import messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from tkinter import ttk

class WLF_GUI(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("WLF Analysis Program")
        self.configure(bg='#2c3e50')  # Modern dark blue background
        
        # Initialize variables to prevent attribute errors
        self.dragging = False
        self.selected_line = None
        self.shifted_data = None
        self.shifted_freqs = None
        self.data = None
        self.estimated_aT_values = None
        
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        self.geometry("{0}x{1}".format(self.screen_width, self.screen_height // 2))
        self.T_data = None
        self.log_aT_data = None
        self.sort_orders = {'C1': False, 'C2': False, 'SSE': False}
        
        # Modern styling
        self.style = ttk.Style()
        self.style.theme_use('clam')  # Use clam theme for modern look
        
        # Configure modern colors and fonts
        self.style.configure('TNotebook', background='#34495e', borderwidth=0)
        self.style.configure('TNotebook.Tab', 
                           font=('Segoe UI', 14, 'bold'),
                           background='#34495e',
                           foreground='#ecf0f1',
                           padding=[20, 10],
                           borderwidth=0)
        self.style.map('TNotebook.Tab',
                      background=[('selected', '#3498db'), ('active', '#2980b9')],
                      foreground=[('selected', '#ffffff'), ('active', '#ffffff')])
        
        self.style.configure('TLabel', 
                           font=('Segoe UI', 12),
                           background='#34495e',
                           foreground='#ecf0f1')
        
        self.style.configure('TButton', 
                           font=('Segoe UI', 12, 'bold'),
                           background='#3498db',
                           foreground='#ffffff',
                           borderwidth=0,
                           padding=[15, 8])
        self.style.map('TButton',
                      background=[('active', '#2980b9'), ('pressed', '#21618c')],
                      foreground=[('active', '#ffffff'), ('pressed', '#ffffff')])
        
        self.style.configure('TFrame', background='#34495e')
        self.style.configure('Treeview', 
                           font=('Segoe UI', 11),
                           background='#2c3e50',
                           foreground='#ecf0f1',
                           fieldbackground='#2c3e50')
        self.style.configure('Treeview.Heading', 
                           font=('Segoe UI', 11, 'bold'),
                           background='#3498db',
                           foreground='#ffffff')
        
        self.create_widgets()

    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.create_step1_tab()
        self.create_step2_3_tab()
        self.create_step4_tab()
        self.create_step5_tab()
        self.create_step6_tab()

    def create_step1_tab(self):
        step1_frame = ttk.Frame(self.notebook)
        self.notebook.add(step1_frame, text="Step 1: Enter Variables")
        
        # Main container with modern styling
        main_container = tk.Frame(step1_frame, bg='#34495e', padx=20, pady=20)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = tk.Label(main_container, 
                              text="WLF Parameters Input", 
                              font=('Segoe UI', 20, 'bold'),
                              bg='#34495e',
                              fg='#ecf0f1')
        title_label.pack(pady=(0, 20))
        
        # Input frame with modern styling
        input_frame = tk.Frame(main_container, bg='#2c3e50', padx=30, pady=30, relief='flat', bd=0)
        input_frame.pack(fill=tk.BOTH, expand=True)
        
        # Headers
        header_frame = tk.Frame(input_frame, bg='#2c3e50')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header_frame, 
                text="Temperature (°C)", 
                font=('Segoe UI', 14, 'bold'),
                bg='#2c3e50',
                fg='#3498db').grid(row=0, column=0, padx=20)
        
        tk.Label(header_frame, 
                text="log(a_T)", 
                font=('Segoe UI', 14, 'bold'),
                bg='#2c3e50',
                fg='#3498db').grid(row=0, column=1, padx=20)

        self.temp_entries = []
        self.log_aT_entries = []
        
        default_temp_values = [0, 10, 20, 40]
        default_log_aT_values = [1.93, 1.3, 0.9, 0]

        # Create entry fields with modern styling
        for i in range(8):
            row_frame = tk.Frame(input_frame, bg='#2c3e50')
            row_frame.pack(fill=tk.X, pady=5)
            
            temp_entry = tk.Entry(row_frame, 
                                width=15, 
                                font=('Segoe UI', 12),
                                bg='#ecf0f1',
                                fg='#2c3e50',
                                relief='flat',
                                bd=0)
            if i < len(default_temp_values):
                temp_entry.insert(0, str(default_temp_values[i]))
            temp_entry.grid(row=0, column=0, padx=20, pady=5)
            self.temp_entries.append(temp_entry)

            log_aT_entry = tk.Entry(row_frame, 
                                  width=15, 
                                  font=('Segoe UI', 12),
                                  bg='#ecf0f1',
                                  fg='#2c3e50',
                                  relief='flat',
                                  bd=0)
            if i < len(default_log_aT_values):
                log_aT_entry.insert(0, str(default_log_aT_values[i]))
            log_aT_entry.grid(row=0, column=1, padx=20, pady=5)
            self.log_aT_entries.append(log_aT_entry)

    def create_step2_3_tab(self):
        step2_3_frame = ttk.Frame(self.notebook)
        self.notebook.add(step2_3_frame, text="Step 2 & 3: WLF Estimation")

        # Left panel for plot
        left_panel = tk.Frame(step2_3_frame, bg='#34495e', padx=15, pady=15)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Plot title
        plot_title = tk.Label(left_panel, 
                             text="WLF Estimation Plot", 
                             font=('Segoe UI', 16, 'bold'),
                             bg='#34495e',
                             fg='#ecf0f1')
        plot_title.pack(pady=(0, 10))

        # Plot frame
        plot_frame = tk.Frame(left_panel, bg='#2c3e50', relief='flat', bd=0)
        plot_frame.pack(fill=tk.BOTH, expand=True)

        self.figure, self.ax = plt.subplots(figsize=(10, 6))
        self.figure.patch.set_facecolor('#2c3e50')
        self.ax.set_facecolor('#2c3e50')
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Sliders frame
        sliders_frame = tk.Frame(left_panel, bg='#34495e')
        sliders_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 0))

        self.c1_slider = tk.Scale(sliders_frame, 
                                 from_=0, to_=1000, 
                                 orient='horizontal', 
                                 label='C1', 
                                 command=self.update_plot, 
                                 bg='#34495e',
                                 fg='#ecf0f1',
                                 font=('Segoe UI', 12),
                                 highlightbackground='#34495e',
                                 troughcolor='#2c3e50',
                                 activebackground='#3498db')
        self.c1_slider.pack(fill='x', pady=5)
        
        self.c2_slider = tk.Scale(sliders_frame, 
                                 from_=0, to_=1000, 
                                 orient='horizontal', 
                                 label='C2', 
                                 command=self.update_plot, 
                                 bg='#34495e',
                                 fg='#ecf0f1',
                                 font=('Segoe UI', 12),
                                 highlightbackground='#34495e',
                                 troughcolor='#2c3e50',
                                 activebackground='#3498db')
        self.c2_slider.pack(fill='x', pady=5)

        # Right panel for controls
        right_panel = tk.Frame(step2_3_frame, bg='#34495e', padx=15, pady=15)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Controls title
        controls_title = tk.Label(right_panel, 
                                 text="WLF C1, C2 Estimation", 
                                 font=('Segoe UI', 16, 'bold'),
                                 bg='#34495e',
                                 fg='#ecf0f1')
        controls_title.pack(pady=(0, 15))

        # Controls frame
        controls_frame = tk.Frame(right_panel, bg='#34495e')
        controls_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 15))

        # Reference temperature input
        temp_frame = tk.Frame(controls_frame, bg='#34495e')
        temp_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(temp_frame, 
                text="Reference Temperature (T_r):", 
                font=('Segoe UI', 12),
                bg='#34495e',
                fg='#ecf0f1').pack(side=tk.LEFT)
        
        self.reference_temp_entry = tk.Entry(temp_frame, 
                                           width=8, 
                                           font=('Segoe UI', 12),
                                           bg='#ecf0f1',
                                           fg='#2c3e50',
                                           relief='flat',
                                           bd=0)
        self.reference_temp_entry.pack(side=tk.LEFT, padx=10)
        self.reference_temp_entry.insert(0, "40")

        # Buttons frame
        buttons_frame = tk.Frame(controls_frame, bg='#34495e')
        buttons_frame.pack(fill=tk.X, pady=10)

        fit_button = tk.Button(buttons_frame, 
                              text="Fit Data", 
                              command=self.fit_data, 
                              height=2, 
                              width=12, 
                              bg='#3498db',
                              fg='#ffffff',
                              font=('Segoe UI', 12, 'bold'),
                              relief='flat',
                              bd=0,
                              activebackground='#2980b9',
                              activeforeground='#ffffff')
        fit_button.pack(side=tk.LEFT, padx=5)

        save_button = tk.Button(buttons_frame, 
                               text="Save to Excel", 
                               command=self.save_to_excel, 
                               height=2, 
                               width=15, 
                               bg='#27ae60',
                               fg='#ffffff',
                               font=('Segoe UI', 12, 'bold'),
                               relief='flat',
                               bd=0,
                               activebackground='#229954',
                               activeforeground='#ffffff')
        save_button.pack(side=tk.LEFT, padx=5)

        # Result label
        self.result_label = tk.Label(controls_frame, 
                                    text="C1: -, C2: -", 
                                    font=('Segoe UI', 14, 'bold'),
                                    bg='#34495e',
                                    fg='#f39c12')
        self.result_label.pack(pady=10)

        # Treeview for results
        tree_frame = tk.Frame(right_panel, bg='#34495e')
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(tree_frame, 
                                columns=('Select', 'C1', 'C2', 'SSE'), 
                                show='headings', 
                                height=15)
        self.tree.heading('Select', text='Select')
        self.tree.heading('C1', text='C1', command=lambda: self.sort_tree_column('C1', False))
        self.tree.heading('C2', text='C2', command=lambda: self.sort_tree_column('C2', False))
        self.tree.heading('SSE', text='SSE', command=lambda: self.sort_tree_column('SSE', False))
        self.tree.column('Select', width=80, anchor='center')
        self.tree.column('C1', width=80, anchor='center')
        self.tree.column('C2', width=80, anchor='center')
        self.tree.column('SSE', width=80, anchor='center')
        self.tree.pack(fill=tk.BOTH, expand=True)

        self.tree.bind('<ButtonRelease-1>', self.on_row_click)

        # SSE explanation
        sse_label = tk.Label(right_panel, 
                            text="SSE = Σ(log(a_T) - fit(log(a_T)))^2", 
                            font=("Segoe UI", 10),
                            bg='#34495e',
                            fg='#bdc3c7')
        sse_label.pack(pady=5)

    def create_step4_tab(self):
        step4_frame = ttk.Frame(self.notebook)
        self.notebook.add(step4_frame, text="Step 4: Estimate aT")

        # Main container
        main_container = tk.Frame(step4_frame, bg='#34495e', padx=20, pady=20)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(main_container, 
                              text="Estimate aT at Desired Temperature", 
                              font=('Segoe UI', 18, 'bold'),
                              bg='#34495e',
                              fg='#ecf0f1')
        title_label.pack(pady=(0, 20))

        # Controls frame
        controls_frame = tk.Frame(main_container, bg='#34495e')
        controls_frame.pack(pady=15, fill=tk.X)

        # Input frame
        input_frame = tk.Frame(controls_frame, bg='#2c3e50', padx=20, pady=20, relief='flat', bd=0)
        input_frame.pack(fill=tk.X)

        tk.Label(input_frame, 
                text="T_Ref_new:", 
                font=('Segoe UI', 12),
                bg='#2c3e50',
                fg='#ecf0f1').pack(side=tk.LEFT, padx=10)
        
        self.new_reference_temp_entry = tk.Entry(input_frame, 
                                               width=8, 
                                               font=('Segoe UI', 12),
                                               bg='#ecf0f1',
                                               fg='#2c3e50',
                                               relief='flat',
                                               bd=0)
        self.new_reference_temp_entry.pack(side=tk.LEFT, padx=10)
        self.new_reference_temp_entry.insert(0, "40")

        # Buttons
        estimate_button = tk.Button(input_frame, 
                                   text="Estimate aT", 
                                   command=self.estimate_aT, 
                                   height=2, 
                                   width=15, 
                                   bg='#3498db',
                                   fg='#ffffff',
                                   font=('Segoe UI', 12, 'bold'),
                                   relief='flat',
                                   bd=0,
                                   activebackground='#2980b9',
                                   activeforeground='#ffffff')
        estimate_button.pack(side=tk.LEFT, padx=10)

        save_estimate_button = tk.Button(input_frame, 
                                        text="Save aT to Excel", 
                                        command=self.save_estimated_aT_to_excel, 
                                        height=2, 
                                        width=18, 
                                        bg='#27ae60',
                                        fg='#ffffff',
                                        font=('Segoe UI', 12, 'bold'),
                                        relief='flat',
                                        bd=0,
                                        activebackground='#229954',
                                        activeforeground='#ffffff')
        save_estimate_button.pack(side=tk.LEFT, padx=10)

        send_aT_button = tk.Button(input_frame, 
                                  text="Send aT to Step 5", 
                                  command=self.send_aT_values, 
                                  height=2, 
                                  width=18, 
                                  bg='#e74c3c',
                                  fg='#ffffff',
                                  font=('Segoe UI', 12, 'bold'),
                                  relief='flat',
                                  bd=0,
                                  activebackground='#c0392b',
                                  activeforeground='#ffffff')
        send_aT_button.pack(side=tk.LEFT, padx=10)

        # Plot frame
        plot_frame = tk.Frame(main_container, bg='#2c3e50', relief='flat', bd=0)
        plot_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))

        self.estimate_figure, self.estimate_ax = plt.subplots(figsize=(10, 6))
        self.estimate_figure.patch.set_facecolor('#2c3e50')
        self.estimate_ax.set_facecolor('#2c3e50')
        self.estimate_canvas = FigureCanvasTkAgg(self.estimate_figure, master=plot_frame)
        self.estimate_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def create_step5_tab(self):
        step5_frame = ttk.Frame(self.notebook)
        self.notebook.add(step5_frame, text="Step 5: Shift Data")

        # Main container
        main_container = tk.Frame(step5_frame, bg='#34495e', padx=20, pady=20)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(main_container, 
                              text="Shift Data Using TTS", 
                              font=('Segoe UI', 18, 'bold'),
                              bg='#34495e',
                              fg='#ecf0f1')
        title_label.pack(pady=(0, 20))

        # Buttons frame
        buttons_frame = tk.Frame(main_container, bg='#34495e')
        buttons_frame.pack(fill=tk.X, pady=(0, 20))

        # Create modern buttons
        button_configs = [
            ("Load Data", self.load_data, '#3498db'),
            ("Shift Data", self.apply_tts, '#27ae60'),
            ("Retrieve aT Values", self.retrieve_aT_values, '#f39c12'),
            ("Save Shifted Data", self.save_shifted_data_to_excel, '#9b59b6'),
            ("Send to Step 6", self.send_to_step6, '#e74c3c'),
            ("Output TTS", self.output_tts, '#1abc9c'),
            ("Smooth Curve", self.smooth_curve, '#34495e')
        ]

        for text, command, color in button_configs:
            btn = tk.Button(buttons_frame, 
                           text=text, 
                           command=command, 
                           height=2, 
                           width=15, 
                           bg=color,
                           fg='#ffffff',
                           font=('Segoe UI', 11, 'bold'),
                           relief='flat',
                           bd=0,
                           activebackground=self.darken_color(color),
                           activeforeground='#ffffff')
            btn.pack(side=tk.LEFT, padx=5, pady=5)

        # Plot frame
        plot_frame = tk.Frame(main_container, bg='#2c3e50', relief='flat', bd=0)
        plot_frame.pack(fill=tk.BOTH, expand=True)

        self.shifted_figure, self.shifted_ax = plt.subplots(figsize=(10, 6))
        self.shifted_figure.patch.set_facecolor('#2c3e50')
        self.shifted_ax.set_facecolor('#2c3e50')
        self.shifted_canvas = FigureCanvasTkAgg(self.shifted_figure, master=plot_frame)
        self.shifted_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Event handlers for dragging
        self.shifted_canvas.mpl_connect('button_press_event', self.on_press)
        self.shifted_canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.shifted_canvas.mpl_connect('button_release_event', self.on_release)

    def create_step6_tab(self):
        step6_frame = ttk.Frame(self.notebook)
        self.notebook.add(step6_frame, text="Step 6: Modify Master Curve")

        # Left panel for main plot
        left_panel = tk.Frame(step6_frame, bg='#34495e', padx=15, pady=15)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(left_panel, 
                              text="Master Curve Modification", 
                              font=('Segoe UI', 16, 'bold'),
                              bg='#34495e',
                              fg='#ecf0f1')
        title_label.pack(pady=(0, 10))

        # Plot frame
        plot_frame = tk.Frame(left_panel, bg='#2c3e50', relief='flat', bd=0)
        plot_frame.pack(fill=tk.BOTH, expand=True)

        self.master_curve_figure, self.master_curve_ax = plt.subplots(figsize=(10, 6))
        self.master_curve_figure.patch.set_facecolor('#2c3e50')
        self.master_curve_ax.set_facecolor('#2c3e50')
        self.master_curve_canvas = FigureCanvasTkAgg(self.master_curve_figure, master=plot_frame)
        self.master_curve_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Right panel for controls
        right_panel = tk.Frame(step6_frame, bg='#34495e', padx=15, pady=15)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)

        # Temperature table
        table_frame = tk.Frame(right_panel, bg='#34495e')
        table_frame.pack(fill=tk.X, pady=(0, 15))

        table_title = tk.Label(table_frame, 
                              text="Temperature Selection", 
                              font=('Segoe UI', 14, 'bold'),
                              bg='#34495e',
                              fg='#ecf0f1')
        table_title.pack(pady=(0, 10))

        self.temp_table = ttk.Treeview(table_frame, 
                                      columns=("Temperature"), 
                                      show='headings', 
                                      height=8)
        self.temp_table.heading("Temperature", text="Temperature (°C)")
        self.temp_table.bind("<ButtonRelease-1>", self.on_table_select)
        self.temp_table.pack(fill=tk.X)

        # Controls frame
        controls_frame = tk.Frame(right_panel, bg='#34495e')
        controls_frame.pack(fill=tk.BOTH, expand=True)

        # Sliders
        sliders_frame = tk.Frame(controls_frame, bg='#34495e')
        sliders_frame.pack(fill=tk.X, pady=10)

        self.at_slider = tk.Scale(sliders_frame, 
                                 from_=0.1, to_=10, 
                                 resolution=0.1, 
                                 orient='horizontal', 
                                 label='aT', 
                                 command=self.update_master_curve, 
                                 bg='#34495e',
                                 fg='#ecf0f1',
                                 font=('Segoe UI', 11),
                                 highlightbackground='#34495e',
                                 troughcolor='#2c3e50',
                                 activebackground='#3498db')
        self.at_slider.pack(fill='x', pady=5)

        self.bt_slider = tk.Scale(sliders_frame, 
                                 from_=0.1, to_=10, 
                                 resolution=0.1, 
                                 orient='horizontal', 
                                 label='bT', 
                                 command=self.update_master_curve, 
                                 bg='#34495e',
                                 fg='#ecf0f1',
                                 font=('Segoe UI', 11),
                                 highlightbackground='#34495e',
                                 troughcolor='#2c3e50',
                                 activebackground='#3498db')
        self.bt_slider.pack(fill='x', pady=5)

        self.sensitivity_slider = tk.Scale(sliders_frame, 
                                          from_=1, to_=10, 
                                          orient='horizontal', 
                                          label='Sensitivity', 
                                          command=self.update_sensitivity, 
                                          bg='#34495e',
                                          fg='#ecf0f1',
                                          font=('Segoe UI', 11),
                                          highlightbackground='#34495e',
                                          troughcolor='#2c3e50',
                                          activebackground='#3498db')
        self.sensitivity_slider.pack(fill='x', pady=5)

        # Axis range controls
        axis_frame = tk.Frame(controls_frame, bg='#34495e')
        axis_frame.pack(fill=tk.X, pady=10)

        axis_title = tk.Label(axis_frame, 
                             text="Axis Range Settings", 
                             font=('Segoe UI', 12, 'bold'),
                             bg='#34495e',
                             fg='#ecf0f1')
        axis_title.pack(pady=(0, 10))

        # X-axis controls
        x_frame = tk.Frame(axis_frame, bg='#34495e')
        x_frame.pack(fill=tk.X, pady=2)

        tk.Label(x_frame, 
                text="X-min:", 
                font=('Segoe UI', 10),
                bg='#34495e',
                fg='#ecf0f1').pack(side=tk.LEFT)
        
        self.x_min_entry = tk.Entry(x_frame, 
                                   width=8, 
                                   font=('Segoe UI', 10),
                                   bg='#ecf0f1',
                                   fg='#2c3e50',
                                   relief='flat',
                                   bd=0)
        self.x_min_entry.pack(side=tk.LEFT, padx=5)
        self.x_min_entry.insert(0, "1e-1")

        tk.Label(x_frame, 
                text="X-max:", 
                font=('Segoe UI', 10),
                bg='#34495e',
                fg='#ecf0f1').pack(side=tk.LEFT, padx=(10, 0))
        
        self.x_max_entry = tk.Entry(x_frame, 
                                   width=8, 
                                   font=('Segoe UI', 10),
                                   bg='#ecf0f1',
                                   fg='#2c3e50',
                                   relief='flat',
                                   bd=0)
        self.x_max_entry.pack(side=tk.LEFT, padx=5)
        self.x_max_entry.insert(0, "1e8")

        # Y-axis controls
        y_frame = tk.Frame(axis_frame, bg='#34495e')
        y_frame.pack(fill=tk.X, pady=2)

        tk.Label(y_frame, 
                text="Y-min:", 
                font=('Segoe UI', 10),
                bg='#34495e',
                fg='#ecf0f1').pack(side=tk.LEFT)
        
        self.y_min_entry = tk.Entry(y_frame, 
                                   width=8, 
                                   font=('Segoe UI', 10),
                                   bg='#ecf0f1',
                                   fg='#2c3e50',
                                   relief='flat',
                                   bd=0)
        self.y_min_entry.pack(side=tk.LEFT, padx=5)
        self.y_min_entry.insert(0, "0.1")

        tk.Label(y_frame, 
                text="Y-max:", 
                font=('Segoe UI', 10),
                bg='#34495e',
                fg='#ecf0f1').pack(side=tk.LEFT, padx=(10, 0))
        
        self.y_max_entry = tk.Entry(y_frame, 
                                   width=8, 
                                   font=('Segoe UI', 10),
                                   bg='#ecf0f1',
                                   fg='#2c3e50',
                                   relief='flat',
                                   bd=0)
        self.y_max_entry.pack(side=tk.LEFT, padx=5)
        self.y_max_entry.insert(0, "1e4")

        # Set axis range button
        axis_button = tk.Button(axis_frame, 
                               text="Set Axis Range", 
                               command=self.update_axis_range, 
                               bg='#3498db',
                               fg='#ffffff',
                               font=('Segoe UI', 10, 'bold'),
                               relief='flat',
                               bd=0,
                               activebackground='#2980b9',
                               activeforeground='#ffffff')
        axis_button.pack(pady=10)

        # T vs aT plot
        at_plot_frame = tk.Frame(controls_frame, bg='#2c3e50', relief='flat', bd=0)
        at_plot_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        at_plot_title = tk.Label(at_plot_frame, 
                                text="T vs aT Plot", 
                                font=('Segoe UI', 12, 'bold'),
                                bg='#2c3e50',
                                fg='#ecf0f1')
        at_plot_title.pack(pady=5)

        self.at_plot_figure, self.at_plot_ax = plt.subplots(figsize=(6, 4))
        self.at_plot_figure.patch.set_facecolor('#2c3e50')
        self.at_plot_ax.set_facecolor('#2c3e50')
        self.at_plot_canvas = FigureCanvasTkAgg(self.at_plot_figure, master=at_plot_frame)
        self.at_plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def darken_color(self, color):
        """Helper function to darken a color for active states"""
        color_map = {
            '#3498db': '#2980b9',
            '#27ae60': '#229954',
            '#f39c12': '#d68910',
            '#9b59b6': '#8e44ad',
            '#e74c3c': '#c0392b',
            '#1abc9c': '#16a085',
            '#34495e': '#2c3e50'
        }
        return color_map.get(color, color)

    def update_axis_range(self):
        x_min = float(self.x_min_entry.get())
        x_max = float(self.x_max_entry.get())
        y_min = float(self.y_min_entry.get())
        y_max = float(self.y_max_entry.get())
        self.master_curve_ax.set_xlim([x_min, x_max])
        self.master_curve_ax.set_ylim([y_min, y_max])
        self.master_curve_canvas.draw()

    def on_table_select(self, event):
        selected_item = self.temp_table.selection()[0]
        selected_temp = self.temp_table.item(selected_item, "values")[0]
        self.selected_temp = float(selected_temp.replace('°C', ''))

        # Initialize sliders
        self.at_slider.set(1)
        self.bt_slider.set(1)
        self.update_master_curve()
        
    def on_temperature_selected(self, event):
        selected_temp = self.temperature_selector.get()
        self.selected_temp = float(selected_temp.replace('°C', ''))
        self.update_master_curve()

    def update_sensitivity(self, event=None):
        self.sensitivity = self.sensitivity_slider.get()

    def send_to_step6(self):
        if not hasattr(self, 'shifted_data') or not hasattr(self, 'shifted_freqs'):
            messagebox.showerror("Error", "Please shift data in Step 5 first.")
            return

        self.loaded_shifted_data = self.shifted_data
        self.loaded_shifted_freqs = self.shifted_freqs

        for temp in self.loaded_shifted_data.columns:
            self.temp_table.insert("", "end", values=(f'{temp}°C'))

        self.plot_master_curve()

    def plot_master_curve(self):
        if not hasattr(self, 'loaded_shifted_data') or not hasattr(self, 'loaded_shifted_freqs'):
            return

        self.master_curve_ax.clear()
        for temp in self.loaded_shifted_data.keys():
            freqs = self.loaded_shifted_freqs[temp]
            data = self.loaded_shifted_data[temp]
            self.master_curve_ax.plot(freqs, data, label=f'{temp}°C')

        self.master_curve_ax.set_xlabel('Shifted Frequency (Hz)', fontsize=8)
        self.master_curve_ax.set_ylabel('Shifted Data (MPa)', fontsize=8)
        self.master_curve_ax.set_xscale('log')
        self.master_curve_ax.set_yscale('log')
        self.update_axis_range()
        self.master_curve_ax.set_title('Master Curve', fontsize=10)
        self.master_curve_ax.legend(fontsize=8)
        self.master_curve_ax.grid(True)

        self.master_curve_canvas.draw()

    def update_master_curve(self, event=None):
        if not hasattr(self, 'loaded_shifted_data') or not hasattr(self, 'loaded_shifted_freqs'):
            return

        aT = self.at_slider.get()
        bT = self.bt_slider.get()

        self.master_curve_ax.clear()
        for temp in self.loaded_shifted_data.keys():
            if float(temp) == self.selected_temp:
                freqs = self.loaded_shifted_freqs[temp] * aT
                data = self.loaded_shifted_data[temp] * bT
                self.master_curve_ax.plot(freqs, data, label=f'{temp}°C', color='green', linewidth=2)
            else:
                freqs = self.loaded_shifted_freqs[temp]
                data = self.loaded_shifted_data[temp]
                self.master_curve_ax.plot(freqs, data, label=f'{temp}°C', color='grey', alpha=0.5)

        self.master_curve_ax.set_xlabel('Shifted Frequency (Hz)', fontsize=8)
        self.master_curve_ax.set_ylabel('Shifted Data (MPa)', fontsize=8)
        self.master_curve_ax.set_xscale('log')
        self.master_curve_ax.set_yscale('log')
        self.update_axis_range()
        self.master_curve_ax.set_title('Adjusted Master Curve', fontsize=10)
        self.master_curve_ax.legend(fontsize=8)
        self.master_curve_ax.grid(True)

        self.master_curve_canvas.draw()

        # Update T vs aT plot
        self.update_at_plot()

        
    def update_at_plot(self):
        if not hasattr(self, 'loaded_shifted_data') or not hasattr(self, 'loaded_shifted_freqs'):
            return

        aT = self.at_slider.get()

        self.at_plot_ax.clear()
        temperatures = sorted([float(temp) for temp in self.loaded_shifted_data.keys()])
        at_values = [aT if float(temp) == self.selected_temp else 1 for temp in temperatures]

        self.at_plot_ax.plot(temperatures, at_values, marker='o', linestyle='-', color='green', label='Adjusted aT')
        self.at_plot_ax.set_xlabel('Temperature (°C)', fontsize=8)
        self.at_plot_ax.set_ylabel('aT', fontsize=8)
        self.at_plot_ax.set_title('T vs aT', fontsize=10)
        self.at_plot_ax.legend(fontsize=8)
        self.at_plot_ax.grid(True)

        self.at_plot_canvas.draw()


    
    def on_press(self, event):
        if event.inaxes is not None:
            self.dragging = True
            self.drag_start_y = event.ydata
            self.drag_start_data = self.shifted_data.copy()

            # Find the nearest line to the mouse click
            self.selected_line = None
            min_distance = float('inf')
            for line in self.shifted_ax.get_lines():
                xdata, ydata = line.get_data()
                distance = np.min(np.abs(ydata - event.ydata))
                if distance < min_distance:
                    min_distance = distance
                    self.selected_line = line

    def on_motion(self, event):
        if self.dragging and event.inaxes is not None and self.selected_line is not None:
            dy = event.ydata - self.drag_start_y
            label = self.selected_line.get_label().replace('°C', '').strip()
            label = float(label)  # Ensure label is numeric to match DataFrame columns
            shift_factor = 10 ** (dy / 100)  # Reduce the sensitivity of the shift
            self.shifted_data[label] = self.drag_start_data[label] * shift_factor
            self.plot_shifted_data()

    def on_release(self, event):
        self.dragging = False
        self.selected_line = None

    def plot_shifted_data(self):
        if self.shifted_data is None or self.shifted_freqs is None:
            return

        self.shifted_ax.clear()
        for temp in self.shifted_data.columns:
            self.shifted_ax.plot(self.shifted_freqs[temp], self.shifted_data[temp], label='{0}°C'.format(temp))

        self.shifted_ax.set_xlabel('Shifted Frequency (Hz)', fontsize=8)
        self.shifted_ax.set_ylabel('Shifted Data (MPa)', fontsize=8)
        self.shifted_ax.set_xscale('log')
        self.shifted_ax.set_yscale('log')
        self.shifted_ax.set_ylim([0.1, 1e4])  # Set a constant range for the y-axis
        self.shifted_ax.set_title('Shifted Data Using TTS', fontsize=10)
        self.shifted_ax.legend(fontsize=8)
        self.shifted_ax.grid(True)

        self.shifted_canvas.draw()

    def save_estimated_aT_to_excel(self):
        if not hasattr(self, 'estimated_aT_values'):
            messagebox.showerror("Error", "No estimated aT values to save. Please estimate aT values in Step 4 first.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel files', '*.xlsx'), ('All files', '*.*')])
        if file_path:
            self.estimated_aT_values.to_excel(file_path, index=False)
            messagebox.showinfo("Save to Excel", "Estimated aT values saved successfully!")

    def save_to_excel(self):
        file_path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel files', '*.xlsx'), ('All files', '*.*')])
        if file_path:
            selected_data = []
            for item in self.tree.get_children():
                if self.tree.set(item, 'Select') == '1':
                    values = self.tree.item(item, 'values')
                    selected_data.append(values)

            if not selected_data:
                messagebox.showerror("Save to Excel", "No data selected.")
                return

            T_r = float(self.reference_temp_entry.get()) + 273.15  # Convert to Kelvin
            # 온도를 5도 간격으로 피팅 (-80°C부터 80°C까지)
            T_fit = np.arange(-80, 81, 5) + 273.15  # Convert to Kelvin

            with pd.ExcelWriter(file_path) as writer:
                for values in selected_data:
                    C1, C2 = int(values[1]), int(values[2])
                    log_aT_fit = self.WLF(T_fit, C1, C2, T_r)
                    aT_fit = 10 ** log_aT_fit
                    fit_df = pd.DataFrame({
                        'Temperature (°C)': T_fit - 273.15,  # Convert to Celsius for saving
                        'log(a_T)': log_aT_fit,
                        'a_T': aT_fit
                    })
                    sheet_name = 'Fit_C1_{0}_C2_{1}'.format(C1, C2)
                    fit_df.to_excel(writer, sheet_name=sheet_name, index=False)

            messagebox.showinfo("Save to Excel", "Data saved successfully!")

    def smooth_curve(self):
        if self.shifted_data is None or self.shifted_freqs is None:
            messagebox.showerror("Error", "Please shift data first.")
            return

        self.shifted_ax.clear()
        for temp in self.shifted_data.columns:
            freqs = self.shifted_freqs[temp]
            data = self.shifted_data[temp]
            spline = UnivariateSpline(np.log(freqs), np.log(data), s=1)
            smoothed_data = np.exp(spline(np.log(freqs)))
            self.shifted_ax.plot(freqs, smoothed_data, label='{0}°C'.format(temp))

        self.shifted_ax.set_xlabel('Shifted Frequency (Hz)', fontsize=8)
        self.shifted_ax.set_ylabel('Shifted Data (MPa)', fontsize=8)
        self.shifted_ax.set_xscale('log')
        self.shifted_ax.set_yscale('log')
        self.shifted_ax.set_ylim([0.1, 1e4])
        self.shifted_ax.set_title('Smoothed Shifted Data Using TTS', fontsize=10)
        self.shifted_ax.legend(fontsize=8)
        self.shifted_ax.grid(True)

        self.shifted_canvas.draw()

    def load_data(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")])
        if not file_path:
            return

        try:
            self.data = pd.read_excel(file_path, index_col=0)
            self.plot_loaded_data()
        except Exception as e:
            messagebox.showerror("Error", "Failed to load data: {0}".format(e))

    def plot_loaded_data(self):
        self.shifted_ax.clear()
        for temp in self.data.columns:
            self.shifted_ax.plot(self.data.index, self.data[temp], label='{0}°C'.format(temp))

        self.shifted_ax.set_xlabel('Frequency (Hz)', fontsize=8)
        self.shifted_ax.set_ylabel('Data', fontsize=8)
        self.shifted_ax.set_title('Loaded Data', fontsize=10)
        self.shifted_ax.legend(fontsize=8)
        self.shifted_ax.grid(True)

        self.shifted_canvas.draw()

    def retrieve_aT_values(self):
        if hasattr(self, 'shift_data_frame') and hasattr(self.shift_data_frame, 'estimated_aT_values'):
            self.estimated_aT_values = self.shift_data_frame.estimated_aT_values
            print("Retrieved aT values in Step 5:")
            print(self.estimated_aT_values)
        else:
            messagebox.showerror("Error", "Please send aT values from Step 4 first.")

    def apply_tts(self):
        if self.data is None:
            messagebox.showerror("Error", "Please load the data first.")
            return

        if not hasattr(self, 'estimated_aT_values'):
            messagebox.showerror("Error", "Please retrieve aT values in Step 5 first.")
            return

        shifted_data = {}
        shifted_freqs = {}

        for temp in self.data.columns:
            try:
                # Find the closest temperature
                closest_temp = min(self.estimated_aT_values['Temperature (°C)'], key=lambda x: abs(x - float(temp)))
                aT = self.estimated_aT_values[self.estimated_aT_values['Temperature (°C)'] == closest_temp]['a_T'].values[0]
            except IndexError:
                messagebox.showerror("Error", "No estimated aT value for temperature {0}°C.".format(temp))
                return

            # Shift the x-axis (frequency) by multiplying with aT
            shifted_freq = self.data.index * aT
            shifted_data[temp] = self.data[temp].values
            shifted_freqs[temp] = shifted_freq

        self.shifted_data = pd.DataFrame(shifted_data)
        self.shifted_freqs = pd.DataFrame(shifted_freqs)

        self.plot_shifted_data()

    def output_tts(self):
        if not hasattr(self, 'shifted_data') or self.shifted_data is None:
            messagebox.showerror("Error", "Please apply TTS first.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel files', '*.xlsx'), ('All files', '*.*')])
        if file_path:
            tts_data = pd.DataFrame({
                'Frequency (Hz)': self.shifted_freqs.values.flatten(),
                'Modulus': self.shifted_data.values.flatten()
            })
            tts_data.to_excel(file_path, index=False)
            messagebox.showinfo("Output TTS", "TTS data saved successfully!")

    def save_shifted_data_to_excel(self):
        if not hasattr(self, 'shifted_data') or not hasattr(self, 'shifted_freqs'):
            messagebox.showerror("Error", "No shifted data to save. Please shift data in Step 5 first.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel files', '*.xlsx'), ('All files', '*.*')])
        if file_path:
            with pd.ExcelWriter(file_path) as writer:
                for temp in self.shifted_data.columns:
                    data_df = pd.DataFrame({
                        'Frequency (Hz)': self.shifted_freqs[temp],
                        'Modulus (MPa)': self.shifted_data[temp]
                    })
                    data_df.to_excel(writer, sheet_name=f'{temp}°C', index=False)
            messagebox.showinfo("Save to Excel", "Shifted data saved successfully!")

    def send_aT_values(self):
        if not hasattr(self, 'estimated_aT_values'):
            estimated_xdata = self.estimate_ax.get_lines()[0].get_xdata()
            estimated_ydata = self.estimate_ax.get_lines()[0].get_ydata()
            self.estimated_aT_values = pd.DataFrame({
                'Temperature (°C)': estimated_xdata,  # Keep the temperatures as decimals
                'a_T': 10 ** estimated_ydata,
                'log(a_T)': estimated_ydata
            })
        if hasattr(self, 'shift_data_frame'):
            self.shift_data_frame.estimated_aT_values = self.estimated_aT_values
        else:
            messagebox.showerror("Error", "Shift data frame not found.")
        if hasattr(self, 'shift_data_frame'):
            self.shift_data_frame.estimated_aT_values = self.estimated_aT_values
            print("aT values sent to Step 5:")
            print(self.shift_data_frame.estimated_aT_values)
        else:
            messagebox.showerror("Error", "Shift data frame not found.")

    def fit_data(self):
        try:
            temperatures = []
            log_aT_values = []

            for temp_entry, log_aT_entry in zip(self.temp_entries, self.log_aT_entries):
                temp = temp_entry.get()
                log_aT = log_aT_entry.get()
                if temp and log_aT:
                    temperatures.append(float(temp))
                    log_aT_values.append(float(log_aT))

            if len(temperatures) != len(log_aT_values):
                raise ValueError("The number of temperatures and log aT values must be the same.")

            self.T_data = np.array(temperatures) + 273.15  # Convert to Kelvin
            self.log_aT_data = np.array(log_aT_values)

            T_r = float(self.reference_temp_entry.get()) + 273.15  # Convert to Kelvin
            initial_guess = [17, 52]

            popt, _ = curve_fit(lambda T, C1, C2: self.WLF(T, int(C1), int(C2), T_r), self.T_data, self.log_aT_data, p0=initial_guess)
            self.C1_fit, self.C2_fit = int(popt[0]), int(popt[1])
            self.result_label.config(text="C1: {0}, C2: {1}".format(self.C1_fit, self.C2_fit))

            self.c1_slider.set(self.C1_fit)
            self.c2_slider.set(self.C2_fit)

            self.perform_grid_search()
            self.update_plot()
        except Exception as e:
            messagebox.showerror("Error", "Failed to fit data: {0}".format(e))

    def WLF(self, T, C1, C2, T_r):
        return -C1 * (T - T_r) / (C2 + (T - T_r))

    def update_plot(self, event=None):
        if self.T_data is None or self.log_aT_data is None:
            return

        T_r = float(self.reference_temp_entry.get()) + 273.15  # Convert to Kelvin
        C1 = self.c1_slider.get()
        C2 = self.c2_slider.get()

        self.ax.clear()
        self.ax.scatter(self.T_data - 273.15, self.log_aT_data, label='Data')  # Convert to Celsius for plotting

        T_fit = np.linspace(-80, 80, 100) + 273.15  # Convert to Kelvin
        log_aT_fit = self.WLF(T_fit, C1, C2, T_r)
        self.ax.plot(T_fit - 273.15, log_aT_fit, label='WLF Fit (C1={0}, C2={1})'.format(C1, C2), color='red')  # Convert to Celsius for plotting

        self.ax.set_xlim([-80, 80])  # x축 범위 설정
        self.ax.set_ylim([min(log_aT_fit) - 1, max(log_aT_fit) + 1])  # y축 범위 설정
        self.ax.set_xlabel('Temperature (°C)', fontsize=8)
        self.ax.set_ylabel('log(a_T)', fontsize=8)
        self.ax.set_title('WLF Fit Comparison', fontsize=10)
        self.ax.legend(fontsize=8)
        self.ax.grid(True)

        self.canvas.draw()

    def perform_grid_search(self):
        if self.T_data is None or self.log_aT_data is None:
            return

        T_r = float(self.reference_temp_entry.get()) + 273.15  # Convert to Kelvin

        # 최적화된 그리드 검색 범위 (실행 시간 단축)
        C1_range = np.arange(0, 200, 5)  # 0-200, 5씩 증가
        C2_range = np.arange(0, 200, 5)  # 0-200, 5씩 증가

        results = []

        self.tree.delete(*self.tree.get_children())

        for C1 in C1_range:
            for C2 in C2_range:
                sse = self.calculate_sse(C1, C2, T_r)
                if not np.isnan(sse):
                    results.append((False, C1, C2, round(sse, 1)))

        results.sort(key=lambda x: x[3])

        for result in results:
            self.tree.insert('', 'end', values=result)

        if results:
            best_params = results[0]
            self.C1_fit, self.C2_fit = best_params[1], best_params[2]
            self.result_label.config(text="C1: {0}, C2: {1}".format(self.C1_fit, self.C2_fit))
            self.c1_slider.set(self.C1_fit)
            self.c2_slider.set(self.C2_fit)
            self.tree.item(self.tree.get_children()[0], tags=('recommended',))
            self.tree.tag_configure('recommended', background='lightgreen')

    def calculate_sse(self, C1, C2, T_r):
        log_aT_fit = self.WLF(self.T_data, C1, C2, T_r)
        sse = np.sum((self.log_aT_data - log_aT_fit) ** 2)
        return sse

    def on_row_click(self, event):
        item = self.tree.selection()[0]
        current_value = self.tree.set(item, 'Select')
        new_value = '1' if current_value == '0' else '0'
        self.tree.set(item, 'Select', new_value)

        self.update_checked_plots()

    def update_checked_plots(self):
        if self.T_data is None or self.log_aT_data is None:
            return

        T_r = float(self.reference_temp_entry.get()) + 273.15  # Convert to Kelvin
        self.ax.clear()
        self.ax.scatter(self.T_data - 273.15, self.log_aT_data, label='Data')  # Convert to Celsius for plotting

        T_fit = np.linspace(-80, 80, 100) + 273.15  # Convert to Kelvin

        colors = ['red', 'blue', 'green', 'orange', 'purple']
        color_index = 0
        log_aT_fit_all = []

        for item in self.tree.get_children():
            if self.tree.set(item, 'Select') == '1':
                values = self.tree.item(item, 'values')
                C1, C2 = int(values[1]), int(values[2])
                log_aT_fit = self.WLF(T_fit, C1, C2, T_r)
                log_aT_fit_all.extend(log_aT_fit)
                self.ax.plot(T_fit - 273.15, log_aT_fit, label='WLF Fit (C1={0}, C2={1})'.format(C1, C2), color=colors[color_index % len(colors)])
                color_index += 1

        self.ax.set_xlim([-80, 80])  # x축 범위 설정
        if log_aT_fit_all:
            self.ax.set_ylim([min(log_aT_fit_all) - 1, max(log_aT_fit_all) + 1])  # y축 범위 설정
        self.ax.set_xlabel('Temperature (°C)', fontsize=8)
        self.ax.set_ylabel('log(a_T)', fontsize=8)
        self.ax.set_title('WLF Fit Comparison', fontsize=10)
        self.ax.legend(fontsize=8)
        self.ax.grid(True)

        self.canvas.draw()

    def estimate_aT(self):
        if self.T_data is None or self.log_aT_data is None:
            return

        T_r_new = float(self.new_reference_temp_entry.get()) + 273.15  # Convert to Kelvin
        T_r = float(self.reference_temp_entry.get()) + 273.15  # Convert to Kelvin

        C1 = self.c1_slider.get()
        C2 = self.c2_slider.get()

        selected_items = [self.tree.item(item) for item in self.tree.get_children() if self.tree.set(item, 'Select') == '1']
        if selected_items:
            C1 = int(selected_items[0]['values'][1])
            C2 = int(selected_items[0]['values'][2])

        T_fit = np.linspace(-80, 80, 100) + 273.15  # Convert to Kelvin
        log_aT_new = self.WLF(T_fit, C1, C2, T_r_new)
        aT_new = 10 ** log_aT_new

        self.estimate_ax.clear()
        self.estimate_ax.scatter(self.T_data - 273.15, self.log_aT_data, label='Original Data')  # Original data
        self.estimate_ax.plot(T_fit - 273.15, log_aT_new, label='Estimated aT (T_r_new={0}°C, C1={1}, C2={2})'.format(T_r_new - 273.15, C1, C2), color='green')  # Estimated data
        self.estimate_ax.plot(T_fit - 273.15, self.WLF(T_fit, C1, C2, T_r), label='Original aT (T_r={0}°C, C1={1}, C2={2})'.format(T_r - 273.15, C1, C2), color='red')  # Original fit data for comparison

        self.estimate_ax.set_xlim([-80, 80])
        self.estimate_ax.set_ylim([-3, 10])  # y축 범위 설정
        self.estimate_ax.set_xlabel('Temperature (°C)', fontsize=8)
        self.estimate_ax.set_ylabel('log(a_T)', fontsize=8)
        self.estimate_ax.set_title('Estimated aT Fit', fontsize=10)
        self.estimate_ax.legend(fontsize=8)
        self.estimate_ax.grid(True)

        self.estimate_canvas.draw()

        # Save estimated aT values to self.estimated_aT_values for later use in Step 5
        self.estimated_aT_values = pd.DataFrame({
            'Temperature (°C)': np.round(T_fit - 273.15).astype(int),  # Convert to Celsius and round to integer
            'a_T': aT_new,
            'log(a_T)': log_aT_new
        })
        print("Estimated aT values:")
        print(self.estimated_aT_values)

    def on_key(self, event):
        if self.selected_label is None or self.selected_index is None:
            return

        shift_amount = 0.1  # Adjust this value to change the step size
        label = self.selected_label.split('°')[0]  # Extract temperature from label
        temp = f"{label}°C"

        if event.key == 'up':
            self.shifted_data[temp][self.selected_index] *= (1 + shift_amount)
        elif event.key == 'down':
            self.shifted_data[temp][self.selected_index] *= (1 - shift_amount)
        elif event.key == 'right':
            self.selected_index = min(self.selected_index + 1, len(self.shifted_data[temp]) - 1)
        elif event.key == 'left':
            self.selected_index = max(self.selected_index - 1, 0)

        self.plot_shifted_data()

if __name__ == "__main__":
    try:
        app = WLF_GUI()
        app.mainloop()
    except Exception as e:
        print(f"Application error: {e}")
