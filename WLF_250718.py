import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
from scipy.interpolate import UnivariateSpline
import tkinter as tk
from tkinter import messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from tkinter import ttk

# ── Color Palette & Style Constants ──────────────────────────────────────────
BG          = '#F5F6FA'   # main background (off-white)
SURFACE     = '#FFFFFF'   # card / panel surface
BORDER      = '#E1E4E8'   # subtle border
TEXT        = '#24292E'    # primary text
TEXT_SEC    = '#586069'    # secondary text
ACCENT      = '#0366D6'   # primary accent (blue)
ACCENT_HVR  = '#0250A3'   # accent hover
SUCCESS     = '#28A745'   # green
SUCCESS_HVR = '#22863A'
DANGER      = '#D73A49'   # red
DANGER_HVR  = '#CB2431'
WARN        = '#F9A825'   # amber
PLOT_BG     = '#FFFFFF'   # plot background
PLOT_GRID   = '#E8EAED'   # plot grid color
import matplotlib.font_manager as _fm
# Pick the first available font for cross-platform support
FONT_FAMILY = 'sans-serif'
for _candidate in ('Segoe UI', 'Helvetica', 'Arial', 'DejaVu Sans'):
    if any(_candidate.lower() in f.name.lower() for f in _fm.fontManager.ttflist):
        FONT_FAMILY = _candidate
        break
plt.rcParams['font.family'] = FONT_FAMILY


class WLF_GUI(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("WLF Analysis Program")
        self.configure(bg=BG)

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

        self._configure_styles()
        self.create_widgets()

    # ── Theme & Style Setup ──────────────────────────────────────────────────
    def _configure_styles(self):
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Notebook
        self.style.configure('TNotebook', background=BG, borderwidth=0)
        self.style.configure('TNotebook.Tab',
                             font=(FONT_FAMILY, 11, 'bold'),
                             background=SURFACE,
                             foreground=TEXT_SEC,
                             padding=[18, 8],
                             borderwidth=0)
        self.style.map('TNotebook.Tab',
                       background=[('selected', ACCENT), ('active', '#DDEAF6')],
                       foreground=[('selected', '#FFFFFF'), ('active', ACCENT)])

        # Labels
        self.style.configure('TLabel',
                             font=(FONT_FAMILY, 11),
                             background=SURFACE,
                             foreground=TEXT)
        self.style.configure('Header.TLabel',
                             font=(FONT_FAMILY, 16, 'bold'),
                             background=SURFACE,
                             foreground=TEXT)
        self.style.configure('SubHeader.TLabel',
                             font=(FONT_FAMILY, 13, 'bold'),
                             background=SURFACE,
                             foreground=TEXT)
        self.style.configure('Muted.TLabel',
                             font=(FONT_FAMILY, 10),
                             background=SURFACE,
                             foreground=TEXT_SEC)

        # Frames
        self.style.configure('TFrame', background=SURFACE)
        self.style.configure('Card.TFrame', background=SURFACE, relief='solid', borderwidth=1)
        self.style.configure('BG.TFrame', background=BG)

        # Buttons
        self.style.configure('Primary.TButton',
                             font=(FONT_FAMILY, 11, 'bold'),
                             background=ACCENT,
                             foreground='#FFFFFF',
                             borderwidth=0,
                             padding=[16, 8])
        self.style.map('Primary.TButton',
                       background=[('active', ACCENT_HVR), ('pressed', ACCENT_HVR)])

        self.style.configure('Success.TButton',
                             font=(FONT_FAMILY, 11, 'bold'),
                             background=SUCCESS,
                             foreground='#FFFFFF',
                             borderwidth=0,
                             padding=[16, 8])
        self.style.map('Success.TButton',
                       background=[('active', SUCCESS_HVR), ('pressed', SUCCESS_HVR)])

        self.style.configure('Danger.TButton',
                             font=(FONT_FAMILY, 11, 'bold'),
                             background=DANGER,
                             foreground='#FFFFFF',
                             borderwidth=0,
                             padding=[16, 8])
        self.style.map('Danger.TButton',
                       background=[('active', DANGER_HVR), ('pressed', DANGER_HVR)])

        self.style.configure('Secondary.TButton',
                             font=(FONT_FAMILY, 11),
                             background='#EDEFF2',
                             foreground=TEXT,
                             borderwidth=0,
                             padding=[16, 8])
        self.style.map('Secondary.TButton',
                       background=[('active', '#DFE1E6'), ('pressed', '#D0D4DB')])

        # Treeview
        self.style.configure('Treeview',
                             font=(FONT_FAMILY, 11),
                             background=SURFACE,
                             foreground=TEXT,
                             fieldbackground=SURFACE,
                             rowheight=28,
                             borderwidth=0)
        self.style.configure('Treeview.Heading',
                             font=(FONT_FAMILY, 11, 'bold'),
                             background='#F1F3F5',
                             foreground=TEXT,
                             borderwidth=1,
                             relief='flat')
        self.style.map('Treeview',
                       background=[('selected', '#DDEAF6')],
                       foreground=[('selected', ACCENT)])

    # ── Helpers ──────────────────────────────────────────────────────────────
    def _make_card(self, parent, **kw):
        """Create a card-like frame with a subtle border."""
        card = tk.Frame(parent, bg=SURFACE, highlightbackground=BORDER,
                        highlightthickness=1, **kw)
        return card

    def _make_entry(self, parent, width=12, default=''):
        """Create a consistently styled entry widget."""
        e = tk.Entry(parent, width=width, font=(FONT_FAMILY, 11),
                     bg=SURFACE, fg=TEXT, relief='solid', bd=1,
                     highlightcolor=ACCENT, highlightthickness=1,
                     insertbackground=TEXT)
        if default:
            e.insert(0, str(default))
        return e

    def _make_button(self, parent, text, command, style='Primary.TButton'):
        return ttk.Button(parent, text=text, command=command, style=style)

    def _setup_plot(self, figsize=(10, 6)):
        """Create a matplotlib figure + axes with clean styling."""
        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor(PLOT_BG)
        ax.set_facecolor(PLOT_BG)
        ax.tick_params(colors=TEXT, labelsize=9)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        for spine in ('bottom', 'left'):
            ax.spines[spine].set_color(BORDER)
        ax.grid(True, color=PLOT_GRID, linewidth=0.5, linestyle='--')
        fig.tight_layout()
        return fig, ax

    def _style_plot(self, ax, xlabel='', ylabel='', title=''):
        """Apply consistent styling after drawing."""
        ax.set_xlabel(xlabel, fontsize=10, color=TEXT, fontfamily=FONT_FAMILY)
        ax.set_ylabel(ylabel, fontsize=10, color=TEXT, fontfamily=FONT_FAMILY)
        if title:
            ax.set_title(title, fontsize=12, fontweight='bold', color=TEXT,
                         fontfamily=FONT_FAMILY, pad=12)
        ax.legend(fontsize=9, frameon=True, fancybox=False,
                  edgecolor=BORDER, framealpha=0.95)
        ax.grid(True, color=PLOT_GRID, linewidth=0.5, linestyle='--')

    def _make_scale(self, parent, label, from_, to_, resolution=1, command=None):
        """Create a consistently styled tk.Scale slider."""
        frame = tk.Frame(parent, bg=SURFACE)
        frame.pack(fill='x', pady=4)
        tk.Label(frame, text=label, font=(FONT_FAMILY, 10, 'bold'),
                 bg=SURFACE, fg=TEXT).pack(anchor='w')
        s = tk.Scale(frame, from_=from_, to_=to_, resolution=resolution,
                     orient='horizontal', command=command,
                     bg=SURFACE, fg=TEXT, font=(FONT_FAMILY, 10),
                     highlightbackground=SURFACE, troughcolor='#E1E4E8',
                     activebackground=ACCENT, length=280, sliderlength=18,
                     bd=0, relief='flat')
        s.pack(fill='x')
        return s

    # ── Widget Creation ──────────────────────────────────────────────────────
    def create_widgets(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=12, pady=(8, 12))

        self.create_step1_tab()
        self.create_step2_3_tab()
        self.create_step4_tab()
        self.create_step5_tab()
        self.create_step6_tab()

    # ── Step 1 ───────────────────────────────────────────────────────────────
    def create_step1_tab(self):
        step1_frame = ttk.Frame(self.notebook, style='BG.TFrame')
        self.notebook.add(step1_frame, text="  Step 1: Enter Variables  ")

        # Center card
        card = self._make_card(step1_frame, padx=32, pady=24)
        card.place(relx=0.5, rely=0.5, anchor='center')

        # Title
        tk.Label(card, text="WLF Parameters Input",
                 font=(FONT_FAMILY, 18, 'bold'), bg=SURFACE, fg=TEXT
                 ).grid(row=0, column=0, columnspan=2, pady=(0, 20))

        # Column headers
        tk.Label(card, text="Temperature (\u00b0C)",
                 font=(FONT_FAMILY, 12, 'bold'), bg=SURFACE, fg=ACCENT
                 ).grid(row=1, column=0, padx=24, pady=(0, 8))
        tk.Label(card, text="log(a\u209c)",
                 font=(FONT_FAMILY, 12, 'bold'), bg=SURFACE, fg=ACCENT
                 ).grid(row=1, column=1, padx=24, pady=(0, 8))

        self.temp_entries = []
        self.log_aT_entries = []

        default_temp_values = [0, 10, 20, 40]
        default_log_aT_values = [1.93, 1.3, 0.9, 0]

        for i in range(8):
            temp_entry = self._make_entry(card, width=16,
                                          default=str(default_temp_values[i]) if i < len(default_temp_values) else '')
            temp_entry.grid(row=i + 2, column=0, padx=24, pady=4)
            self.temp_entries.append(temp_entry)

            log_aT_entry = self._make_entry(card, width=16,
                                            default=str(default_log_aT_values[i]) if i < len(default_log_aT_values) else '')
            log_aT_entry.grid(row=i + 2, column=1, padx=24, pady=4)
            self.log_aT_entries.append(log_aT_entry)

    # ── Step 2 & 3 ──────────────────────────────────────────────────────────
    def create_step2_3_tab(self):
        step2_3_frame = ttk.Frame(self.notebook, style='BG.TFrame')
        self.notebook.add(step2_3_frame, text="  Step 2 & 3: WLF Estimation  ")

        # ── Left: Plot ──
        left_panel = tk.Frame(step2_3_frame, bg=BG)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(12, 6), pady=12)

        plot_card = self._make_card(left_panel, padx=12, pady=12)
        plot_card.pack(fill=tk.BOTH, expand=True)

        tk.Label(plot_card, text="WLF Estimation Plot",
                 font=(FONT_FAMILY, 14, 'bold'), bg=SURFACE, fg=TEXT
                 ).pack(anchor='w', pady=(0, 8))

        self.figure, self.ax = self._setup_plot(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_card)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Sliders
        slider_card = self._make_card(left_panel, padx=16, pady=12)
        slider_card.pack(fill=tk.X, pady=(8, 0))

        self.c1_slider = self._make_scale(slider_card, 'C1', 0, 1000,
                                          command=self.update_plot)
        self.c2_slider = self._make_scale(slider_card, 'C2', 0, 1000,
                                          command=self.update_plot)

        # ── Right: Controls ──
        right_panel = tk.Frame(step2_3_frame, bg=BG)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(6, 12), pady=12)

        ctrl_card = self._make_card(right_panel, padx=16, pady=16)
        ctrl_card.pack(fill=tk.X)

        tk.Label(ctrl_card, text="WLF C1, C2 Estimation",
                 font=(FONT_FAMILY, 14, 'bold'), bg=SURFACE, fg=TEXT
                 ).pack(anchor='w', pady=(0, 12))

        # Reference temperature
        ref_frame = tk.Frame(ctrl_card, bg=SURFACE)
        ref_frame.pack(fill=tk.X, pady=4)
        tk.Label(ref_frame, text="Reference Temperature (T\u1d63):",
                 font=(FONT_FAMILY, 11), bg=SURFACE, fg=TEXT
                 ).pack(side=tk.LEFT)
        self.reference_temp_entry = self._make_entry(ref_frame, width=8, default='40')
        self.reference_temp_entry.pack(side=tk.LEFT, padx=(8, 0))

        # Buttons
        btn_frame = tk.Frame(ctrl_card, bg=SURFACE)
        btn_frame.pack(fill=tk.X, pady=(12, 8))
        self._make_button(btn_frame, "Fit Data", self.fit_data,
                          'Primary.TButton').pack(side=tk.LEFT, padx=(0, 6))
        self._make_button(btn_frame, "Save to Excel", self.save_to_excel,
                          'Success.TButton').pack(side=tk.LEFT)

        # Result label
        self.result_label = tk.Label(ctrl_card, text="C1: \u2014   C2: \u2014",
                                     font=(FONT_FAMILY, 14, 'bold'),
                                     bg=SURFACE, fg=ACCENT)
        self.result_label.pack(anchor='w', pady=(8, 12))

        # Treeview
        tree_card = self._make_card(right_panel, padx=8, pady=8)
        tree_card.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        self.tree = ttk.Treeview(tree_card,
                                 columns=('Select', 'C1', 'C2', 'SSE'),
                                 show='headings', height=15)
        self.tree.heading('Select', text='Sel')
        self.tree.heading('C1', text='C1',
                          command=lambda: self.sort_tree_column('C1', False))
        self.tree.heading('C2', text='C2',
                          command=lambda: self.sort_tree_column('C2', False))
        self.tree.heading('SSE', text='SSE',
                          command=lambda: self.sort_tree_column('SSE', False))
        self.tree.column('Select', width=50, anchor='center')
        self.tree.column('C1', width=80, anchor='center')
        self.tree.column('C2', width=80, anchor='center')
        self.tree.column('SSE', width=90, anchor='center')

        scrollbar = ttk.Scrollbar(tree_card, orient='vertical',
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind('<ButtonRelease-1>', self.on_row_click)

        # SSE note
        tk.Label(right_panel, text="SSE = \u03a3(log(a\u209c) \u2212 fit)²",
                 font=(FONT_FAMILY, 10), bg=BG, fg=TEXT_SEC
                 ).pack(anchor='w', pady=(6, 0), padx=8)

    # ── Step 4 ───────────────────────────────────────────────────────────────
    def create_step4_tab(self):
        step4_frame = ttk.Frame(self.notebook, style='BG.TFrame')
        self.notebook.add(step4_frame, text="  Step 4: Estimate a\u209c  ")

        wrapper = tk.Frame(step4_frame, bg=BG)
        wrapper.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Top controls card
        ctrl_card = self._make_card(wrapper, padx=20, pady=16)
        ctrl_card.pack(fill=tk.X)

        tk.Label(ctrl_card, text="Estimate a\u209c at Desired Temperature",
                 font=(FONT_FAMILY, 14, 'bold'), bg=SURFACE, fg=TEXT
                 ).pack(anchor='w', pady=(0, 12))

        row = tk.Frame(ctrl_card, bg=SURFACE)
        row.pack(fill=tk.X)

        tk.Label(row, text="T_Ref_new:", font=(FONT_FAMILY, 11),
                 bg=SURFACE, fg=TEXT).pack(side=tk.LEFT)
        self.new_reference_temp_entry = self._make_entry(row, width=8, default='40')
        self.new_reference_temp_entry.pack(side=tk.LEFT, padx=(8, 16))

        self._make_button(row, "Estimate a\u209c", self.estimate_aT,
                          'Primary.TButton').pack(side=tk.LEFT, padx=(0, 6))
        self._make_button(row, "Save a\u209c to Excel",
                          self.save_estimated_aT_to_excel,
                          'Success.TButton').pack(side=tk.LEFT, padx=(0, 6))
        self._make_button(row, "Send a\u209c to Step 5", self.send_aT_values,
                          'Danger.TButton').pack(side=tk.LEFT)

        # Plot card
        plot_card = self._make_card(wrapper, padx=12, pady=12)
        plot_card.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.estimate_figure, self.estimate_ax = self._setup_plot(figsize=(10, 6))
        self.estimate_canvas = FigureCanvasTkAgg(self.estimate_figure,
                                                  master=plot_card)
        self.estimate_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ── Step 5 ───────────────────────────────────────────────────────────────
    def create_step5_tab(self):
        step5_frame = ttk.Frame(self.notebook, style='BG.TFrame')
        self.notebook.add(step5_frame, text="  Step 5: Shift Data  ")

        wrapper = tk.Frame(step5_frame, bg=BG)
        wrapper.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # Buttons card
        btn_card = self._make_card(wrapper, padx=20, pady=16)
        btn_card.pack(fill=tk.X)

        tk.Label(btn_card, text="Shift Data Using TTS",
                 font=(FONT_FAMILY, 14, 'bold'), bg=SURFACE, fg=TEXT
                 ).pack(anchor='w', pady=(0, 12))

        btn_row = tk.Frame(btn_card, bg=SURFACE)
        btn_row.pack(fill=tk.X)

        button_configs = [
            ("Load Data",          self.load_data,                 'Primary.TButton'),
            ("Shift Data",         self.apply_tts,                 'Success.TButton'),
            ("Retrieve a\u209c",   self.retrieve_aT_values,        'Secondary.TButton'),
            ("Save Shifted Data",  self.save_shifted_data_to_excel, 'Secondary.TButton'),
            ("Send to Step 6",     self.send_to_step6,             'Danger.TButton'),
            ("Output TTS",         self.output_tts,                'Secondary.TButton'),
            ("Smooth Curve",       self.smooth_curve,              'Secondary.TButton'),
        ]

        for text, command, bstyle in button_configs:
            self._make_button(btn_row, text, command, bstyle
                              ).pack(side=tk.LEFT, padx=(0, 6), pady=2)

        # Plot card
        plot_card = self._make_card(wrapper, padx=12, pady=12)
        plot_card.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.shifted_figure, self.shifted_ax = self._setup_plot(figsize=(10, 6))
        self.shifted_canvas = FigureCanvasTkAgg(self.shifted_figure,
                                                 master=plot_card)
        self.shifted_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.shifted_canvas.mpl_connect('button_press_event', self.on_press)
        self.shifted_canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.shifted_canvas.mpl_connect('button_release_event', self.on_release)

    # ── Step 6 ───────────────────────────────────────────────────────────────
    def create_step6_tab(self):
        step6_frame = ttk.Frame(self.notebook, style='BG.TFrame')
        self.notebook.add(step6_frame, text="  Step 6: Modify Master Curve  ")

        # ── Left: Master curve plot ──
        left_panel = tk.Frame(step6_frame, bg=BG)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True,
                        padx=(12, 6), pady=12)

        plot_card = self._make_card(left_panel, padx=12, pady=12)
        plot_card.pack(fill=tk.BOTH, expand=True)

        tk.Label(plot_card, text="Master Curve",
                 font=(FONT_FAMILY, 14, 'bold'), bg=SURFACE, fg=TEXT
                 ).pack(anchor='w', pady=(0, 8))

        self.master_curve_figure, self.master_curve_ax = self._setup_plot(
            figsize=(10, 6))
        self.master_curve_canvas = FigureCanvasTkAgg(
            self.master_curve_figure, master=plot_card)
        self.master_curve_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # ── Right: Controls ──
        right_panel = tk.Frame(step6_frame, bg=BG, width=320)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(6, 12), pady=12)
        right_panel.pack_propagate(False)

        # Temperature table
        table_card = self._make_card(right_panel, padx=12, pady=12)
        table_card.pack(fill=tk.X)

        tk.Label(table_card, text="Temperature Selection",
                 font=(FONT_FAMILY, 12, 'bold'), bg=SURFACE, fg=TEXT
                 ).pack(anchor='w', pady=(0, 8))

        self.temp_table = ttk.Treeview(table_card, columns=("Temperature"),
                                        show='headings', height=8)
        self.temp_table.heading("Temperature", text="Temperature (\u00b0C)")
        self.temp_table.bind("<ButtonRelease-1>", self.on_table_select)
        self.temp_table.pack(fill=tk.X)

        # Sliders
        slider_card = self._make_card(right_panel, padx=12, pady=12)
        slider_card.pack(fill=tk.X, pady=(8, 0))

        self.at_slider = self._make_scale(slider_card, 'a\u209c', 0.1, 10,
                                          resolution=0.1,
                                          command=self.update_master_curve)
        self.bt_slider = self._make_scale(slider_card, 'b\u209c', 0.1, 10,
                                          resolution=0.1,
                                          command=self.update_master_curve)
        self.sensitivity_slider = self._make_scale(slider_card, 'Sensitivity',
                                                   1, 10,
                                                   command=self.update_sensitivity)

        # Axis range
        axis_card = self._make_card(right_panel, padx=12, pady=12)
        axis_card.pack(fill=tk.X, pady=(8, 0))

        tk.Label(axis_card, text="Axis Range",
                 font=(FONT_FAMILY, 11, 'bold'), bg=SURFACE, fg=TEXT
                 ).pack(anchor='w', pady=(0, 8))

        xr = tk.Frame(axis_card, bg=SURFACE)
        xr.pack(fill=tk.X, pady=2)
        tk.Label(xr, text="X-min:", font=(FONT_FAMILY, 10),
                 bg=SURFACE, fg=TEXT_SEC).pack(side=tk.LEFT)
        self.x_min_entry = self._make_entry(xr, width=8, default='1e-1')
        self.x_min_entry.pack(side=tk.LEFT, padx=(4, 12))
        tk.Label(xr, text="X-max:", font=(FONT_FAMILY, 10),
                 bg=SURFACE, fg=TEXT_SEC).pack(side=tk.LEFT)
        self.x_max_entry = self._make_entry(xr, width=8, default='1e8')
        self.x_max_entry.pack(side=tk.LEFT, padx=4)

        yr = tk.Frame(axis_card, bg=SURFACE)
        yr.pack(fill=tk.X, pady=2)
        tk.Label(yr, text="Y-min:", font=(FONT_FAMILY, 10),
                 bg=SURFACE, fg=TEXT_SEC).pack(side=tk.LEFT)
        self.y_min_entry = self._make_entry(yr, width=8, default='0.1')
        self.y_min_entry.pack(side=tk.LEFT, padx=(4, 12))
        tk.Label(yr, text="Y-max:", font=(FONT_FAMILY, 10),
                 bg=SURFACE, fg=TEXT_SEC).pack(side=tk.LEFT)
        self.y_max_entry = self._make_entry(yr, width=8, default='1e4')
        self.y_max_entry.pack(side=tk.LEFT, padx=4)

        self._make_button(axis_card, "Set Axis Range",
                          self.update_axis_range,
                          'Primary.TButton').pack(fill=tk.X, pady=(8, 0))

        # T vs aT plot
        at_card = self._make_card(right_panel, padx=8, pady=8)
        at_card.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

        tk.Label(at_card, text="T vs a\u209c",
                 font=(FONT_FAMILY, 11, 'bold'), bg=SURFACE, fg=TEXT
                 ).pack(anchor='w', pady=(0, 4))

        self.at_plot_figure, self.at_plot_ax = self._setup_plot(figsize=(5, 3))
        self.at_plot_canvas = FigureCanvasTkAgg(self.at_plot_figure,
                                                 master=at_card)
        self.at_plot_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ═════════════════════════════════════════════════════════════════════════
    # Business Logic  (unchanged)
    # ═════════════════════════════════════════════════════════════════════════

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
        self.selected_temp = float(selected_temp.replace('\u00b0C', ''))

        self.at_slider.set(1)
        self.bt_slider.set(1)
        self.update_master_curve()

    def on_temperature_selected(self, event):
        selected_temp = self.temperature_selector.get()
        self.selected_temp = float(selected_temp.replace('\u00b0C', ''))
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
            self.temp_table.insert("", "end", values=(f'{temp}\u00b0C'))

        self.plot_master_curve()

    def plot_master_curve(self):
        if not hasattr(self, 'loaded_shifted_data') or not hasattr(self, 'loaded_shifted_freqs'):
            return

        self.master_curve_ax.clear()
        for temp in self.loaded_shifted_data.keys():
            freqs = self.loaded_shifted_freqs[temp]
            data = self.loaded_shifted_data[temp]
            self.master_curve_ax.plot(freqs, data, label=f'{temp}\u00b0C')

        self._style_plot(self.master_curve_ax,
                         xlabel='Shifted Frequency (Hz)',
                         ylabel='Shifted Data (MPa)',
                         title='Master Curve')
        self.master_curve_ax.set_xscale('log')
        self.master_curve_ax.set_yscale('log')
        self.update_axis_range()
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
                self.master_curve_ax.plot(freqs, data,
                                          label=f'{temp}\u00b0C',
                                          color=ACCENT, linewidth=2)
            else:
                freqs = self.loaded_shifted_freqs[temp]
                data = self.loaded_shifted_data[temp]
                self.master_curve_ax.plot(freqs, data,
                                          label=f'{temp}\u00b0C',
                                          color='#C0C0C0', alpha=0.5)

        self._style_plot(self.master_curve_ax,
                         xlabel='Shifted Frequency (Hz)',
                         ylabel='Shifted Data (MPa)',
                         title='Adjusted Master Curve')
        self.master_curve_ax.set_xscale('log')
        self.master_curve_ax.set_yscale('log')
        self.update_axis_range()
        self.master_curve_canvas.draw()

        self.update_at_plot()

    def update_at_plot(self):
        if not hasattr(self, 'loaded_shifted_data') or not hasattr(self, 'loaded_shifted_freqs'):
            return

        aT = self.at_slider.get()

        self.at_plot_ax.clear()
        temperatures = sorted([float(temp) for temp in self.loaded_shifted_data.keys()])
        at_values = [aT if float(temp) == self.selected_temp else 1 for temp in temperatures]

        self.at_plot_ax.plot(temperatures, at_values, marker='o', linestyle='-',
                             color=ACCENT, label='Adjusted a\u209c')
        self._style_plot(self.at_plot_ax,
                         xlabel='Temperature (\u00b0C)',
                         ylabel='a\u209c',
                         title='T vs a\u209c')
        self.at_plot_canvas.draw()

    def on_press(self, event):
        if event.inaxes is not None:
            self.dragging = True
            self.drag_start_y = event.ydata
            self.drag_start_data = self.shifted_data.copy()

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
            label = self.selected_line.get_label().replace('\u00b0C', '').strip()
            label = float(label)
            shift_factor = 10 ** (dy / 100)
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
            self.shifted_ax.plot(self.shifted_freqs[temp],
                                self.shifted_data[temp],
                                label='{0}\u00b0C'.format(temp))

        self._style_plot(self.shifted_ax,
                         xlabel='Shifted Frequency (Hz)',
                         ylabel='Shifted Data (MPa)',
                         title='Shifted Data Using TTS')
        self.shifted_ax.set_xscale('log')
        self.shifted_ax.set_yscale('log')
        self.shifted_ax.set_ylim([0.1, 1e4])
        self.shifted_canvas.draw()

    def save_estimated_aT_to_excel(self):
        if not hasattr(self, 'estimated_aT_values'):
            messagebox.showerror("Error", "No estimated a\u209c values to save. Please estimate a\u209c values in Step 4 first.")
            return

        file_path = filedialog.asksaveasfilename(defaultextension='.xlsx', filetypes=[('Excel files', '*.xlsx'), ('All files', '*.*')])
        if file_path:
            self.estimated_aT_values.to_excel(file_path, index=False)
            messagebox.showinfo("Save to Excel", "Estimated a\u209c values saved successfully!")

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

            T_r = float(self.reference_temp_entry.get()) + 273.15
            T_fit = np.arange(-80, 81, 5) + 273.15

            with pd.ExcelWriter(file_path) as writer:
                for values in selected_data:
                    C1, C2 = int(values[1]), int(values[2])
                    log_aT_fit = self.WLF(T_fit, C1, C2, T_r)
                    aT_fit = 10 ** log_aT_fit
                    fit_df = pd.DataFrame({
                        'Temperature (\u00b0C)': T_fit - 273.15,
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
            self.shifted_ax.plot(freqs, smoothed_data,
                                label='{0}\u00b0C'.format(temp))

        self._style_plot(self.shifted_ax,
                         xlabel='Shifted Frequency (Hz)',
                         ylabel='Shifted Data (MPa)',
                         title='Smoothed Shifted Data Using TTS')
        self.shifted_ax.set_xscale('log')
        self.shifted_ax.set_yscale('log')
        self.shifted_ax.set_ylim([0.1, 1e4])
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
            self.shifted_ax.plot(self.data.index, self.data[temp],
                                label='{0}\u00b0C'.format(temp))

        self._style_plot(self.shifted_ax,
                         xlabel='Frequency (Hz)',
                         ylabel='Data',
                         title='Loaded Data')
        self.shifted_canvas.draw()

    def retrieve_aT_values(self):
        if hasattr(self, 'shift_data_frame') and hasattr(self.shift_data_frame, 'estimated_aT_values'):
            self.estimated_aT_values = self.shift_data_frame.estimated_aT_values
            print("Retrieved aT values in Step 5:")
            print(self.estimated_aT_values)
        else:
            messagebox.showerror("Error", "Please send a\u209c values from Step 4 first.")

    def apply_tts(self):
        if self.data is None:
            messagebox.showerror("Error", "Please load the data first.")
            return

        if not hasattr(self, 'estimated_aT_values'):
            messagebox.showerror("Error", "Please retrieve a\u209c values in Step 5 first.")
            return

        shifted_data = {}
        shifted_freqs = {}

        for temp in self.data.columns:
            try:
                closest_temp = min(self.estimated_aT_values['Temperature (\u00b0C)'], key=lambda x: abs(x - float(temp)))
                aT = self.estimated_aT_values[self.estimated_aT_values['Temperature (\u00b0C)'] == closest_temp]['a_T'].values[0]
            except IndexError:
                messagebox.showerror("Error", "No estimated a\u209c value for temperature {0}\u00b0C.".format(temp))
                return

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
                    data_df.to_excel(writer, sheet_name=f'{temp}\u00b0C', index=False)
            messagebox.showinfo("Save to Excel", "Shifted data saved successfully!")

    def send_aT_values(self):
        if not hasattr(self, 'estimated_aT_values'):
            estimated_xdata = self.estimate_ax.get_lines()[0].get_xdata()
            estimated_ydata = self.estimate_ax.get_lines()[0].get_ydata()
            self.estimated_aT_values = pd.DataFrame({
                'Temperature (\u00b0C)': estimated_xdata,
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

            self.T_data = np.array(temperatures) + 273.15
            self.log_aT_data = np.array(log_aT_values)

            T_r = float(self.reference_temp_entry.get()) + 273.15
            initial_guess = [17, 52]

            popt, _ = curve_fit(lambda T, C1, C2: self.WLF(T, int(C1), int(C2), T_r), self.T_data, self.log_aT_data, p0=initial_guess)
            self.C1_fit, self.C2_fit = int(popt[0]), int(popt[1])
            self.result_label.config(text="C1: {0}   C2: {1}".format(self.C1_fit, self.C2_fit))

            self.c1_slider.set(self.C1_fit)
            self.c2_slider.set(self.C2_fit)

            self.perform_grid_search()
            self.update_plot()
        except Exception as e:
            messagebox.showerror("Error", "Failed to fit data: {0}".format(e))

    def WLF(self, T, C1, C2, T_r):
        denom = C2 + (T - T_r)
        with np.errstate(divide='ignore', invalid='ignore'):
            result = np.where(denom == 0, np.nan, -C1 * (T - T_r) / denom)
        return result

    def update_plot(self, event=None):
        if self.T_data is None or self.log_aT_data is None:
            return

        T_r = float(self.reference_temp_entry.get()) + 273.15
        C1 = self.c1_slider.get()
        C2 = self.c2_slider.get()

        self.ax.clear()
        self.ax.scatter(self.T_data - 273.15, self.log_aT_data,
                        label='Data', color=ACCENT, zorder=5, s=50,
                        edgecolors='white', linewidths=0.8)

        T_fit = np.linspace(-80, 80, 100) + 273.15
        log_aT_fit = self.WLF(T_fit, C1, C2, T_r)
        self.ax.plot(T_fit - 273.15, log_aT_fit,
                     label='WLF Fit (C1={0}, C2={1})'.format(C1, C2),
                     color=DANGER, linewidth=1.8)

        self.ax.set_xlim([-80, 80])
        finite = log_aT_fit[np.isfinite(log_aT_fit)]
        if len(finite) > 0:
            self.ax.set_ylim([finite.min() - 1, finite.max() + 1])
        self._style_plot(self.ax,
                         xlabel='Temperature (\u00b0C)',
                         ylabel='log(a\u209c)',
                         title='WLF Fit Comparison')
        self.canvas.draw()

    def perform_grid_search(self):
        if self.T_data is None or self.log_aT_data is None:
            return

        T_r = float(self.reference_temp_entry.get()) + 273.15

        C1_range = np.arange(0, 200, 5)
        C2_range = np.arange(0, 200, 5)

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
            self.result_label.config(text="C1: {0}   C2: {1}".format(self.C1_fit, self.C2_fit))
            self.c1_slider.set(self.C1_fit)
            self.c2_slider.set(self.C2_fit)
            self.tree.item(self.tree.get_children()[0], tags=('recommended',))
            self.tree.tag_configure('recommended', background='#DDEAF6')

    def calculate_sse(self, C1, C2, T_r):
        log_aT_fit = self.WLF(self.T_data, C1, C2, T_r)
        sse = np.nansum((self.log_aT_data - log_aT_fit) ** 2)
        return sse

    def sort_tree_column(self, col, reverse):
        data = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        try:
            data.sort(key=lambda t: float(t[0]), reverse=reverse)
        except ValueError:
            data.sort(key=lambda t: t[0], reverse=reverse)
        for index, (_, k) in enumerate(data):
            self.tree.move(k, '', index)
        self.sort_orders[col] = not reverse
        self.tree.heading(col, command=lambda: self.sort_tree_column(col, not reverse))

    def on_row_click(self, event):
        item = self.tree.selection()[0]
        current_value = self.tree.set(item, 'Select')
        new_value = '1' if current_value == '0' else '0'
        self.tree.set(item, 'Select', new_value)

        self.update_checked_plots()

    def update_checked_plots(self):
        if self.T_data is None or self.log_aT_data is None:
            return

        T_r = float(self.reference_temp_entry.get()) + 273.15
        self.ax.clear()
        self.ax.scatter(self.T_data - 273.15, self.log_aT_data,
                        label='Data', color=ACCENT, zorder=5, s=50,
                        edgecolors='white', linewidths=0.8)

        T_fit = np.linspace(-80, 80, 100) + 273.15

        colors = [DANGER, '#6F42C1', SUCCESS, '#F97316', '#0EA5E9']
        color_index = 0
        log_aT_fit_all = []

        for item in self.tree.get_children():
            if self.tree.set(item, 'Select') == '1':
                values = self.tree.item(item, 'values')
                C1, C2 = int(values[1]), int(values[2])
                log_aT_fit = self.WLF(T_fit, C1, C2, T_r)
                log_aT_fit_all.extend(log_aT_fit)
                self.ax.plot(T_fit - 273.15, log_aT_fit,
                             label='WLF Fit (C1={0}, C2={1})'.format(C1, C2),
                             color=colors[color_index % len(colors)],
                             linewidth=1.8)
                color_index += 1

        self.ax.set_xlim([-80, 80])
        if log_aT_fit_all:
            finite = [v for v in log_aT_fit_all if np.isfinite(v)]
            if finite:
                self.ax.set_ylim([min(finite) - 1, max(finite) + 1])
        self._style_plot(self.ax,
                         xlabel='Temperature (\u00b0C)',
                         ylabel='log(a\u209c)',
                         title='WLF Fit Comparison')
        self.canvas.draw()

    def estimate_aT(self):
        if self.T_data is None or self.log_aT_data is None:
            return

        T_r_new = float(self.new_reference_temp_entry.get()) + 273.15
        T_r = float(self.reference_temp_entry.get()) + 273.15

        C1 = self.c1_slider.get()
        C2 = self.c2_slider.get()

        selected_items = [self.tree.item(item) for item in self.tree.get_children() if self.tree.set(item, 'Select') == '1']
        if selected_items:
            C1 = int(selected_items[0]['values'][1])
            C2 = int(selected_items[0]['values'][2])

        T_fit = np.linspace(-80, 80, 100) + 273.15
        log_aT_new = self.WLF(T_fit, C1, C2, T_r_new)
        aT_new = 10 ** log_aT_new

        self.estimate_ax.clear()
        self.estimate_ax.scatter(self.T_data - 273.15, self.log_aT_data,
                                 label='Original Data', color=ACCENT, zorder=5,
                                 s=50, edgecolors='white', linewidths=0.8)
        self.estimate_ax.plot(T_fit - 273.15, log_aT_new,
                              label='Estimated a\u209c (T_r_new={0}\u00b0C, C1={1}, C2={2})'.format(T_r_new - 273.15, C1, C2),
                              color=SUCCESS, linewidth=1.8)
        self.estimate_ax.plot(T_fit - 273.15, self.WLF(T_fit, C1, C2, T_r),
                              label='Original a\u209c (T_r={0}\u00b0C, C1={1}, C2={2})'.format(T_r - 273.15, C1, C2),
                              color=DANGER, linewidth=1.8)

        self.estimate_ax.set_xlim([-80, 80])
        self.estimate_ax.set_ylim([-3, 10])
        self._style_plot(self.estimate_ax,
                         xlabel='Temperature (\u00b0C)',
                         ylabel='log(a\u209c)',
                         title='Estimated a\u209c Fit')
        self.estimate_canvas.draw()

        self.estimated_aT_values = pd.DataFrame({
            'Temperature (\u00b0C)': np.round(T_fit - 273.15).astype(int),
            'a_T': aT_new,
            'log(a_T)': log_aT_new
        })
        print("Estimated aT values:")
        print(self.estimated_aT_values)

    def on_key(self, event):
        if self.selected_label is None or self.selected_index is None:
            return

        shift_amount = 0.1
        label = self.selected_label.split('\u00b0')[0]
        temp = f"{label}\u00b0C"

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
