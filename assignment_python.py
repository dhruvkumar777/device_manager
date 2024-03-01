import sqlite3
import random
import time
import matplotlib.pyplot as plt
import xlsxwriter
import datetime
#from statistics import mean
from collections import Counter
import xlrd
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

    #def get_status(self):
    #    return self.device.DO1, self.device.DO2, self.device.Tx
    def get_status(self):
        conn = sqlite3.connect(self.db_filename)
        c = conn.cursor()
        c.execute('''SELECT * FROM readings WHERE serial_number = (SELECT MAX(serial_number) FROM readings)''')
        data = c.fetchall()
        conn.close()

        if not data:
            print("No data available. Setting all readings to 0.")
            print("DO1:", self.device.DO1)
            print("DO2:", self.device.DO2)
            print("Tx:", self.device.Tx)
            return

        for row in data:
            print("DO1:", row[5])
            print("DO2:", row[6])
            print("Tx:", row[7])


    def calculate_mode(self, data):
        # Count occurrences of each value
        counts = Counter(data)
        # Get the most common value(s)
        mode_values = counts.most_common(1)
        if mode_values:  # Check if there are mode values
            mode_value, mode_count = mode_values[0]
            return mode_value 
        else:
            return None
    def get_specific_date_trend(self, selected_date):
        conn = sqlite3.connect(self.db_filename)
        c = conn.cursor()

        c.execute("SELECT timestamp, DO1, DO2,Tx FROM readings WHERE date = ? ORDER BY timestamp",
                  (selected_date,))
        data = c.fetchall()
        conn.close()

        timestamps = [row[0] for row in data]
        DO1_values = [row[1] for row in data]
        DO2_values = [row[2] for row in data]
        Tx_values  = [row[3] for row in data]

        return timestamps, DO1_values, DO2_values,Tx_values
    def get_date_range_trend(self, start_date, end_date):
        conn = sqlite3.connect(self.db_filename)
        c = conn.cursor()

        c.execute("SELECT date, DO1, DO2 ,Tx FROM readings WHERE date >= ? AND date <= ? ORDER BY date",
              (start_date, end_date))
        data = c.fetchall()
        conn.close()

        date_dict = {}  # Dictionary to store DO1, DO2, and Tx values for each date
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
       # print(number_list,average)
        return average       
    def calculate_mode_for_dates(self, date_dict):
        dates = []
        do1_modes = []
        do2_modes = []
        tx_modes = []
    
        for date, values in date_dict.items():
            if not values:
                continue
        
            # Calculate mode for DO1 and DO2
            do1_mode = self.calculate_mode(values['DO1'])
            do2_mode = self.calculate_mode(values['DO2'])
            tx_mode = self.calculate_average(values['Tx'])
            # Append results to lists
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
        date = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        c.execute("INSERT INTO readings (timestamp, date, A, B, DO1, DO2, Tx) VALUES (?, ?, ?, ?, ?, ?, ?)",
                  (timestamp, date, self.device.A, self.device.B, self.device.DO1, self.device.DO2, self.device.Tx))
        conn.commit()
        conn.close()


    def log_readings_to_excel(self):
        workbook = xlsxwriter.Workbook(self.excel_filename)
        worksheet = workbook.add_worksheet()

        # Write header
        header = ['Timestamp', 'Date', 'A', 'B', 'DO1', 'DO2', 'Tx']
        for col, item in enumerate(header):
            worksheet.write(0, col, item)

        # Write data
        conn = sqlite3.connect(self.db_filename)
        c = conn.cursor()
        c.execute("SELECT timestamp, date, A, B, DO1, DO2, Tx FROM readings ORDER BY timestamp")
        data = c.fetchall()
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                worksheet.write(row_idx + 1, col_idx, cell_data)

        workbook.close()
    def plot_weekly_trends_2d(self, start_date, end_date):
        dates, DO1_values, DO2_values, Tx_values = self.calculate_mode_for_dates(self.get_date_range_trend(start_date, end_date))

        # Plot DO1 and DO2
        plt.plot(dates, DO1_values, marker='o', label='DO1')
        plt.plot(dates, DO2_values, marker='s', label='DO2', linestyle='dashed')
        plt.xlabel('Date')
        plt.ylabel('Value')
        plt.title('Weekly Trends of DO1 and DO2')
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.show()

        # Plot temperature (Tx)
        plt.plot(dates, Tx_values, marker='x', label='Temperature')
        plt.xlabel('Date')
        plt.ylabel('Temperature')
        plt.title('Temperature Trend')
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.show()
    def plot_specific_date_trends_2d(self, selected_date):
        timestamps, DO1_values, DO2_values, Tx_values = self.get_specific_date_trend(selected_date)
        if not timestamps:
            print("No data available for the selected date.")
            return

        timestamps = [datetime.datetime.fromtimestamp(ts) for ts in timestamps]
        print(timestamps,DO1_values, DO2_values, Tx_values)

        # Plot DO1 and DO2
        plt.plot(timestamps, DO1_values, marker='o', label='DO1')
        plt.plot(timestamps, DO2_values, marker='s', label='DO2', linestyle='dashed')
        plt.xlabel('TIMESTAMP')
        plt.ylabel('Value')
        plt.title('Trends of DO1 and DO2')
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.show()

        # Plot temperature (Tx)
        plt.plot(timestamps, Tx_values, marker='x', label='Temperature')
        plt.xlabel('TIMESTAMP')
        plt.ylabel('Temperature')
        plt.title('Temperature Trend')
        plt.xticks(rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.show()

'''def convert_excel_date(excel_date):
    return excel_date.strftime('%Y-%m-%d')

def add_sample_data_to_excel(workbook, date, A, B, DO1, DO2, Tx, timestamp):
    worksheet = workbook.get_worksheet_by_name('Sheet1')
    row = worksheet.dim_rowmax + 1

    worksheet.write(row, 0, '{:.5f}'.format(timestamp))
    worksheet.write(row, 1,convert_excel_date( date))
    worksheet.write(row, 2, A)
    worksheet.write(row, 3, B)
    worksheet.write(row, 4, DO1)
    worksheet.write(row, 5, DO2)
    worksheet.write(row, 6, Tx)'''



def print_options():
    print("\nOptions:")
    print("1. Get Current Status")
    print("2. Configure Inputs (A and B)")
    print("3. Get Weekly Trends")
    print("4. Get Trends for specific range")
    print("5. Get Trends for Specific Date")
    print("6. Download Excel Report")
    print("7. Exit")

def main():
    tekx_simulator = TekXSimulator()
    db_filename = "tekx_readings8.db"
    excel_filename = "tekx_readings8.xlsx"

    device_manager = DeviceManager(tekx_simulator, db_filename, excel_filename)
   # add_sample_data_for_one_week(device_manager,excel_filename)

    while True:
        print_options()
        choice = input("Enter your choice: ")

        if choice == '1':
            print("Current Status:")
            device_manager.get_status()
            #print("DO1: {}, DO2: {}, Tx: {}".format(DO1, DO2, Tx))
        elif choice == '2':
            while True:
                try:
                    A = int(input("Enter value for A (0 or 1): "))
                    if A not in (0, 1):
                        raise ValueError("Input must be 0 or 1")
            
                    B = int(input("Enter value for B (0 or 1): "))
                    if B not in (0, 1):
                        raise ValueError("Input must be 0 or 1")
            
            # If inputs are valid, break out of the loop
                    break
            
                except ValueError as e:
                    print("Invalid input:", e)
            device_manager.set_inputs(A, B)
            print("Inputs A and B configured successfully.")
        elif choice == '3':
            start_date = datetime.datetime.now() - datetime.timedelta(days=7)
            end_date = datetime.datetime.now()
            device_manager.plot_weekly_trends_2d( start_date, end_date)
        elif choice == '4':
            start_date=input("Enter the start date in 'YYYY-MM-DD' format: ")
            end_date=input("Enter the end date in 'YYYY-MM-DD' format: ")
            #start_date = datetime.datetime.now() - datetime.timedelta(days=7)
            #end_date = datetime.datetime.now()
            device_manager.plot_weekly_trends_2d( start_date, end_date)
        elif choice == '5':
            selected_date = input("Enter the date (YYYY-MM-DD): ")
            device_manager.plot_specific_date_trends_2d(selected_date)
        elif choice == '6':
            device_manager.log_readings_to_excel()
            print("Excel report downloaded successfully.")
        elif choice == '7':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
