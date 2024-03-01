import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random
import sqlite3
import xlsxwriter
from collections import Counter
import time


class TekXSimulator:
    def __init__(self):
        self.A = 0
        self.B = 0
        self.DO1 = 0
        self.DO2 = 0
        self.Tx = 0.0  

    def update_status(self):
        self.DO1 = random.randint(0, 1)
        self.DO2 = random.randint(0, 1)
        self.Tx = round(random.uniform(20, 30), 2)  # Simulated temperature reading

class DeviceManager:
    def __init__(self, device, db_filename, excel_filename):
        self.device = device
        self.db_filename = db_filename
        self.excel_filename = excel_filename
        self.create_db()

    def set_inputs(self, A, B):
        self.device.A = A
        self.device.B = B
        self.device.update_status()
        self.log_readings()
        self.log_readings_to_excel()

    def get_status(self):
        conn = sqlite3.connect(self.db_filename)
        c = conn.cursor()
        c.execute('''SELECT * FROM readings WHERE serial_number = (SELECT MAX(serial_number) FROM readings)''')
        data = c.fetchall()
        conn.close()

        if not data:
            return self.device.DO1,self.device.DO2,self.device.Tx

        for row in data:
            return row[5],row[6],row[7]

    def calculate_mode(self, data):
        counts = Counter(data)
        mode_values = counts.most_common(1)
        if mode_values:  
            mode_value, mode_count = mode_values[0]
            return mode_value 
        else:
            return None

    def get_specific_date_trend(self, selected_date):
        conn = sqlite3.connect(self.db_filename)
        c = conn.cursor()

        c.execute("SELECT timestamp, DO1, DO2, Tx FROM readings WHERE date = ? ORDER BY timestamp",
                  (selected_date,))
        data = c.fetchall()
        conn.close()

        timestamps = [row[0] for row in data]
        DO1_values = [row[1] for row in data]
        DO2_values = [row[2] for row in data]
        Tx_values  = [row[3] for row in data]

        return timestamps, DO1_values, DO2_values, Tx_values

    def get_date_range_trend(self, start_date, end_date):
        conn = sqlite3.connect(self.db_filename)
        c = conn.cursor()

        c.execute("SELECT date, DO1, DO2, Tx FROM readings WHERE date >= ? AND date <= ? ORDER BY date",
                  (start_date, end_date))
        data = c.fetchall()
        conn.close()

        date_dict = {}
        for row in data:
            date = row[0]
            DO1_value = row[1]
            DO2_value = row[2]
            tx_value = row[3]
            if date not in date_dict:
                date_dict[date] = {'DO1': [], 'DO2': [], 'Tx': []}
        
            date_dict[date]['DO1'].append(DO1_value)
            date_dict[date]['DO2'].append(DO2_value)
            date_dict[date]['Tx'].append(tx_value)
        return date_dict
    def calculate_average(self,number_list):
        if not number_list:
            return 0
        
        total = sum(number_list)
        average = total / len(number_list)
        #print(number_list,average)
        return average        
    def calculate_mode_for_dates(self, date_dict):
        dates = []
        do1_modes = []
        do2_modes = []
        tx_modes = []
    
        for date, values in date_dict.items():
            if not values:
                continue
        
            do1_mode = self.calculate_mode(values['DO1'])
            do2_mode = self.calculate_mode(values['DO2'])
            tx_mode = self.calculate_average(values['Tx'])
            dates.append(date)
            do1_modes.append(do1_mode)
            do2_modes.append(do2_mode)
            tx_modes.append(tx_mode)
    
        return dates, do1_modes, do2_modes, tx_modes

    def create_db(self):
        conn = sqlite3.connect(self.db_filename)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS readings
                     (serial_number INTEGER PRIMARY KEY AUTOINCREMENT,
                      timestamp REAL, date TEXT, A INTEGER, B INTEGER,
                      DO1 INTEGER, DO2 INTEGER, Tx REAL)''')
        conn.commit()
        conn.close()

    def log_readings(self):
        conn = sqlite3.connect(self.db_filename)
        c = conn.cursor()
        timestamp = time.time()
        date = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        c.execute("INSERT INTO readings (timestamp, date, A, B, DO1, DO2, Tx) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (timestamp, date, self.device.A, self.device.B, self.device.DO1, self.device.DO2, self.device.Tx))
        conn.commit()
        conn.close()

    def log_readings_to_excel(self):
        workbook = xlsxwriter.Workbook(self.excel_filename)
        worksheet = workbook.add_worksheet()

        header = ['Timestamp', 'Date', 'A', 'B', 'DO1', 'DO2', 'Tx']
        for col, item in enumerate(header):
            worksheet.write(0, col, item)

        conn = sqlite3.connect(self.db_filename)
        c = conn.cursor()
        c.execute("SELECT timestamp, date, A, B, DO1, DO2, Tx FROM readings ORDER BY timestamp")
        data = c.fetchall()
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                worksheet.write(row_idx + 1, col_idx, cell_data)

        workbook.close()

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TekX Simulator")
        self.geometry("600x600")

        self.tekx_simulator = TekXSimulator()
        self.db_filename = "tekx_readings8.db"
        self.excel_filename = "tekx_readings8.xlsx"
        self.device_manager = DeviceManager(self.tekx_simulator, self.db_filename, self.excel_filename)

        self.create_widgets()

    def create_widgets(self):
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill=tk.BOTH, expand=True)

        self.tab1 = ttk.Frame(self.tabs)
        self.tabs.add(self.tab1, text="Status")

        self.tab2 = ttk.Frame(self.tabs)
        self.tabs.add(self.tab2, text="Configure Inputs")

        self.tab3 = ttk.Frame(self.tabs)
        self.tabs.add(self.tab3, text="Weekly Trends")

        self.tab4 = ttk.Frame(self.tabs)
        self.tabs.add(self.tab4, text="Specific Date Trends")

        self.tab5 = ttk.Frame(self.tabs)
        self.tabs.add(self.tab5, text=" Excel Report")

        self.tab6 = ttk.Frame(self.tabs)
        self.tabs.add(self.tab6, text="Exit")
        self.tab7 = ttk.Frame(self.tabs)
        self.tabs.add(self.tab7, text="Date Range")

        self.create_tab1()
        self.create_tab2()
        self.create_tab3()
        self.create_tab4()
        self.create_tab5()
        self.create_tab6()
        self.create_tab7()

    def create_tab1(self):
        lbl_status = tk.Label(self.tab1, text="Current Status", font=('Helvetica', 16))
        lbl_status.pack(pady=10)

        btn_get_status = tk.Button(self.tab1, text="Get Current Status", command=self.get_current_status)
        btn_get_status.pack()

        self.lbl_result = tk.Label(self.tab1, text="", font=('Helvetica', 12))
        self.lbl_result.pack(pady=10)

    def create_tab2(self):
        lbl_config = tk.Label(self.tab2, text="Configure Inputs", font=('Helvetica', 16))
        lbl_config.pack(pady=10)

        lbl_A = tk.Label(self.tab2, text="Value for A (0 or 1): ")
        lbl_A.pack()
        self.entry_A = tk.Entry(self.tab2)
        self.entry_A.pack()

        lbl_B = tk.Label(self.tab2, text="Value for B (0 or 1): ")
        lbl_B.pack()
        self.entry_B = tk.Entry(self.tab2)
        self.entry_B.pack()

        btn_configure = tk.Button(self.tab2, text="Configure", command=self.configure_inputs)
        btn_configure.pack(pady=10)

    def create_tab3(self):
        lbl_weekly_trends = tk.Label(self.tab3, text="Weekly Trends", font=('Helvetica', 16))
        lbl_weekly_trends.pack(pady=10)

        btn_plot_trends = tk.Button(self.tab3, text="Plot Weekly Trends", command=self.plot_weekly_trends)
        btn_plot_trends.pack()

    def create_tab4(self):
        lbl_specific_date = tk.Label(self.tab4, text="Specific Date Trends", font=('Helvetica', 16))
        lbl_specific_date.pack(pady=10)

        lbl_date = tk.Label(self.tab4, text="Enter the date (YYYY-MM-DD): ")
        lbl_date.pack()
        self.entry_date = tk.Entry(self.tab4)
        self.entry_date.pack()

        btn_plot_specific_date = tk.Button(self.tab4, text="Plot Trends for Specific Date", command=self.plot_specific_date_trends)
        btn_plot_specific_date.pack(pady=10)

    def create_tab5(self):
        lbl_excel_report = tk.Label(self.tab5, text="Download Excel Report", font=('Helvetica', 16))
        lbl_excel_report.pack(pady=10)

        btn_download_excel = tk.Button(self.tab5, text="Download", command=self.download_excel_report)
        btn_download_excel.pack()

    def create_tab6(self):
        lbl_exit = tk.Label(self.tab6, text="Exit Application", font=('Helvetica', 16))
        lbl_exit.pack(pady=10)

        btn_exit = tk.Button(self.tab6, text="Exit", command=self.destroy)
        btn_exit.pack()
    
    def create_tab7(self):
        lbl_specific_date_range = tk.Label(self.tab7, text="Trends for Specific Date Range", font=('Helvetica', 16))
        lbl_specific_date_range.pack(pady=10)

        lbl_start_date = tk.Label(self.tab7, text="Start Date (YYYY-MM-DD): ")
        lbl_start_date.pack()
        self.entry_start_date = tk.Entry(self.tab7)
        self.entry_start_date.pack()

        lbl_end_date = tk.Label(self.tab7, text="End Date (YYYY-MM-DD): ")
        lbl_end_date.pack()
        self.entry_end_date = tk.Entry(self.tab7)
        self.entry_end_date.pack()

        btn_plot_specific_date_range = tk.Button(self.tab7, text="Plot Trends for Specific Date Range", command=self.plot_specific_date_range_trends)
        btn_plot_specific_date_range.pack(pady=10)
    def get_current_status(self):
        DO1, DO2, Tx = self.device_manager.get_status()
        self.lbl_result.config(text=f"DO1: {DO1}, DO2: {DO2}, Tx: {Tx}")

    def configure_inputs(self):
        A = int(self.entry_A.get())
        B = int(self.entry_B.get())
        if A not in (0, 1) or B not in (0, 1):
            messagebox.showerror("Error", "Invalid input. A and B must be either 0 or 1.")
            return
        self.device_manager.set_inputs(A, B)
        messagebox.showinfo("Success", "Inputs A and B configured successfully.")
    def plot_specific_date_range_trends(self):
        start_date = self.entry_start_date.get()
        end_date = self.entry_end_date.get()

        if not start_date or not end_date:
            messagebox.showerror("Error", "Please enter both start and end dates.")
            return

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD.")
            return

        if start_date > end_date:
            messagebox.showerror("Error", "Start date cannot be after end date.")
            return

        date_dict = self.device_manager.get_date_range_trend(start_date, end_date)
        if not date_dict:
            messagebox.showerror("Error", "No data available for the selected date range.")
            return

        dates, DO1_values, DO2_values, Tx_values = self.device_manager.calculate_mode_for_dates(date_dict)

        # Clear existing canvas widgets
        for widget in self.tab7.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.destroy()

        # Create a frame for the canvas
        plot_frame = tk.Frame(self.tab7)
        plot_frame.pack(fill=tk.BOTH, expand=True)

        # Create the first subplot for DO1 and DO2
        fig, ax = plt.subplots()
        ax.plot(dates, DO1_values, marker='o', label='DO1')
        ax.plot(dates, DO2_values, marker='s', label='DO2', linestyle='dashed')
        ax.set_xlabel('Date')
        ax.set_ylabel('Value')
        ax.set_title('Trends of DO1 and DO2')
        ax.legend()
        fig.autofmt_xdate()

        # Create the second subplot for Temperature
        fig2, ax2 = plt.subplots()
        ax2.plot(dates, Tx_values, marker='x', label='Temperature')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Temperature')
        ax2.set_title('Temperature Trend')
        ax2.legend()
        fig2.autofmt_xdate()

        # Create canvas for the first subplot
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create canvas for the second subplot
        canvas2 = FigureCanvasTkAgg(fig2, master=plot_frame)
        canvas2.draw()
        canvas_widget2 = canvas2.get_tk_widget()
        canvas_widget2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    def plot_weekly_trends(self):
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now()
        dates, DO1_values, DO2_values, Tx_values = self.device_manager.calculate_mode_for_dates(
            self.device_manager.get_date_range_trend(start_date, end_date))

        # Clear existing canvas widgets
        for widget in self.tab3.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.destroy()

        # Create a frame for the canvas
        plot_frame = tk.Frame(self.tab3)
        plot_frame.pack(fill=tk.BOTH, expand=True)

        # Create the first subplot for DO1 and DO2
        fig, ax = plt.subplots()
        ax.plot(dates, DO1_values, marker='o', label='DO1')
        ax.plot(dates, DO2_values, marker='s', label='DO2', linestyle='dashed')
        ax.set_xlabel('Date')
        ax.set_ylabel('Value')
        ax.set_title('Weekly Trends of DO1 and DO2')
        ax.legend()
        fig.autofmt_xdate()

        # Create the second subplot for Temperature
        fig2, ax2 = plt.subplots()
        ax2.plot(dates, Tx_values, marker='x', label='Temperature')
        ax2.set_xlabel('Date')
        ax2.set_ylabel('Temperature')
        ax2.set_title('Temperature Trend')
        ax2.legend()
        fig2.autofmt_xdate()

        # Create canvas for the first subplot
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create canvas for the second subplot
        canvas2 = FigureCanvasTkAgg(fig2, master=plot_frame)
        canvas2.draw()
        canvas_widget2 = canvas2.get_tk_widget()
        canvas_widget2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    def plot_specific_date_trends(self):
        selected_date = self.entry_date.get()
        if not selected_date:
            messagebox.showerror("Error", "Please enter a valid date.")
            return
        timestamps, DO1_values, DO2_values, Tx_values = self.device_manager.get_specific_date_trend(selected_date)
        if not timestamps:
            messagebox.showerror("Error", "No data available for the selected date.")
            return

        # Clear existing canvas widgets
        for widget in self.tab4.winfo_children():
            if isinstance(widget, tk.Frame):
                widget.destroy()

        # Create a frame for the canvas
        plot_frame = tk.Frame(self.tab4)
        plot_frame.pack(fill=tk.BOTH, expand=True)

        # Create the first subplot for DO1 and DO2
        fig, ax = plt.subplots()
        timestamps = [datetime.fromtimestamp(ts) for ts in timestamps]
        ax.plot(timestamps, DO1_values, marker='o', label='DO1')
        ax.plot(timestamps, DO2_values, marker='s', label='DO2', linestyle='dashed')
        ax.set_xlabel('Timestamp')
        ax.set_ylabel('Value')
        ax.set_title('Trends of DO1 and DO2')
        ax.legend()
        fig.autofmt_xdate()

        # Create the second subplot for Temperature
        fig2, ax2 = plt.subplots()
        ax2.plot(timestamps, Tx_values, marker='x', label='Temperature')
        ax2.set_xlabel('Timestamp')
        ax2.set_ylabel('Temperature')
        ax2.set_title('Temperature Trend')
        ax2.legend()
        fig2.autofmt_xdate()

        # Create canvas for the first subplot
        canvas = FigureCanvasTkAgg(fig, master=plot_frame)
        canvas.draw()
        canvas_widget = canvas.get_tk_widget()
        canvas_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Create canvas for the second subplot
        canvas2 = FigureCanvasTkAgg(fig2, master=plot_frame)
        canvas2.draw()
        canvas_widget2 = canvas2.get_tk_widget()
        canvas_widget2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def download_excel_report(self):
        self.device_manager.log_readings_to_excel()
        messagebox.showinfo("Success", "Excel report downloaded successfully.")

if __name__ == "__main__":
    app = Application()
    app.mainloop()
