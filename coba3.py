##### How To plot serial data on python GUI###
from collections import deque
import datetime
import queue
import random
import threading
from tkinter import filedialog, messagebox, ttk
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import tkinter as tk 
import numpy as np
import serial as sr
from PIL import ImageGrab
from serial.tools import list_ports
import time
import pandas as pd
import csv

### Main Gui Code###
root=tk.Tk()
root.configure(bg="pink")
root.geometry("1024x768")
root.title("Fotodetektor UV")
##--Create frame for graphic--##
main_frame=tk.Frame(root, bg="white")
main_frame.grid(row=0,column=1,sticky="ne",padx=10,pady=10)
##--Create frame for Buttons--##
button_frame=tk.Frame(root, bg="pink")
button_frame.grid(row=0, column=0, rowspan=2, sticky="nw", padx=10, pady=10)
##--Create frame for table--##
table_frame=tk.Frame(root, bg="pink")
table_frame.grid(row=1, column=1, sticky="se", padx=10, pady=10)

###
input_frame=tk.Frame(root,bg="pink")
input_frame.grid(row=0, column=0,padx=10,pady=10)
###


##--Function to start & stop the animation--##
def plot_start():
    global animation, running, ser, delay_time, scanning_time, kernel_size
    if ser:
        ser.close()
    ser_port=port_var.get()
    try:
        delay_time=float(delay_time_var.get())
        scanning_time=int(scanning_time_var.get())
        kernel_size=int(kernel_size_var.get())
        if delay_time<=0 or scanning_time<=0 or kernel_size<=0:
            raise ValueError("Delay time, scanning time,kernel size must be positive values and input the right port") 
    except ValueError as e:
        messagebox.showerror("Input Error", str(e))
        return
    animation=FuncAnimation(fig, update_plot, fargs=(kernel_size,), interval=1000,cache_frame_data=False)
    notification=f"Delay Time:{delay_time}s\nScanning Time:{scanning_time}s\nKernelSize:{kernel_size}"
    messagebox.showinfo("Setting Set", notification)
    ser=sr.Serial(ser_port, 9600)
    running=True
    animation=FuncAnimation(fig, update_plot, fargs=(kernel_size,), interval=1000,cache_frame_data=False)
    read_thread=threading.Thread(target=read_serial, daemon=True)
    read_thread.start()
    stop_thread=threading.Thread(target=stop_acquisition_after_time, daemon=True)
    stop_thread.start()
    plt.show()
##
def plot_stop():
    global running, ser
    running=False
    if ser:
        ser.close()
def update_delay_time():
    global delay_time
    delay_time=float(delay_time_entry.get())
    messagebox.showinfo("Info", f"delay time {delay_time}s ")
def update_scanning_time():
    global max_data_points, intensity_data, x_data
    max_data_points=int(scanning_time_entry.get())
    intensity_data=deque(intensity_data, maxlen=max_data_points)
    x_data=deque(x_data, maxlen=max_data_points)
    messagebox.showinfo("Info", f"scanning time {max_data_points}m")
def detect_serial_ports():
    available_ports=list(list_ports.comports()) 
    port_options=[port.device for port in available_ports]
    return port_options

data_ready_event=threading.Event()
data_queue=queue.Queue()

def connect_serial():
    global ser
    port=port_entry.get()
    try:
        ser = sr.Serial(port, baudrate=9600, timeout=1)
        ser.reset_input_buffer() 
        messagebox.showinfo("Info", f"Connected to {port}")
    except Exception as e:
        messagebox.showerror("Error", f"Error connecting to {port}: {e}")
def read_serial():
    global running,scr
    while running:
        if ser and ser.in_waiting>0:
            data=ser.readline().decode('utf-8').strip()
            process_data(data)
        time.sleep(delay_time)     
timestamp_data=deque(maxlen=1000)
smoothed_intensity_data=deque(maxlen=1000)
def process_data(data):
    try:
        if data.startswith("Tegangan:"):
            intensity_str=data.split(":")[1].split()[0]
            intensity=float(intensity_str)
            intensity_data.append(intensity)
            timestamp=datetime.now()
            timestamp_data.append(timestamp)
        else:
            print("Output", data)
    except ValueError:
        print("Invalid data:", data)      
def update_plot(frame, kernel_size):
    ax.clear()
    ax.xaxis.set_major_formatter(plt.FuncFormatter(format_x_ticks))
    x_values=list(timestamp_data)
    if len(intensity_data)>=kernel_size:
        y_values_smoothed=pd.Series(intensity_data).rolling(window=kernel_size).mean()
        y_values_smoothed=y_values_smoothed.tolist()
    else:
        y_values_smoothed=[None]*len(intensity_data)
    ax.plot(x_values, y_values_smoothed, marker='o', color='b')
    ax.set_xlabel("Time")
    ax.set_ylabel("Intensiity (W/m2)")
    ax.set_title("Real-Time Intensity")
    ax.relim()
    ax.autoscale_view()
    canvas.draw()
def format_x_ticks(value, tick_number):
    if x_data and tick_number is not None and 0<=tick_number<len(x_data):
        dt=x_data[-1]-x_data[0]
        total_seconds=dt.total_seconds()
        if total_seconds<60:
            return x_data[tick_number].strftimr("%H:%M:%S")
        elif total_seconds<3600:
            return x_data[tick_number].strftime("%H:%M")
        else:
            return x_data[tick_number].strftime("%T-%m-%d %H:%M")
    else:
        return""
scanning_time=0
def show_scanning_done_popup():
    messagebox.showinfo("Info", "Done")
def stop_acquisition_after_time():
    global scanning_time, running
    if scanning_time>0:
        time.sleep(scanning_time*60)
        running=False
        if ser:
            ser.close()
        show_scanning_done_popup()
                            
#data=np.array([])
#cond=False

#def plot_data():
    #global cond, intensity_data, x_data
    #if cond:
       #read_serial()
       #lines.set_xdata(np.arrange(len(intensity_data)))
       #lines.set_ydata(intensity_data)
       #ax.relim()
       #ax.autoscale_view()
       #canvas.draw()
#root.after(1,plot_data)  
       
def print_results():
    messagebox.showinfo("Info", f"Success to print and saved as images")
    save_graph_and_table()
def exit_application():
    if ser.is_open:
        ser.close()
    root.quit()
    root.destroy()    
def save_graph_and_table():
    save_dir=filedialog.askdirectory()
    if not save_dir:
        return
    graph_bbox=(canvas_widget.winfo_rootx(),canvas_widget.winfo_rooty(),canvas_widget.winfo_rootx()+canvas_widget.winfo_width(),canvas_widget.winfo_rooty()+canvas_widget.winfo_height())
    graph_image=ImageGrab.grab(bbox=graph_bbox)
    graph_image_path=f"{save_dir}/graph_image.png"
    graph_image.save(graph_image_path)
    table_bbox=(table_frame.winfo_rootx(),table_frame.winfo_rooty(),table_frame.winfo_rootx()+table_frame.winfo_width(),table_frame.winfo_rooty()+table_frame.winfo_height())
    table_image=ImageGrab.grab(bbox=table_bbox)
    table_image_path=f"{save_dir}/table_image.png"
    table_image.save(table_image_path)
    messagebox.showinfo("Info", "Graph and table saved as images in{save_dir}.")
def reset_settings():
    global delay_time, scanning_time, kernel_size_var, intensity_data, x_data, timestamp_data
    delay_time=1
    scanning_time=0
    kernel_size_var.set("3")
    intensity_data.clear()
    x_data.clear()
    ax.clear()
    canvas.draw()
    messagebox.showinfo("Info", "Reset to Deafult Values")
           

##---Create plot onbject on GUI--##
fig=Figure();
ax=fig.add_subplot(111)
canvas=FigureCanvasTkAgg(fig, master=main_frame)
canvas_widget=canvas.get_tk_widget()
canvas_widget.grid(row=0, column=0, sticky="nsew")
##--adjust maxlen as needed--##
intensity_data=deque(maxlen=1000)
max_data_points=1000
x_data=deque(maxlen=max_data_points)
animation=None
running=False
ser=None
delay_time=1
##--Create table--##
tree=ttk.Treeview(table_frame, column=("Intensity", "Time"), selectmode="extended")
tree.heading("#0", text="N0.")
tree.heading("Intensity", text="Intensity")
tree.heading("Time", text="Time")
tree.pack(side="right", fill="both", expand=True)
tree_scroll=ttk.Scrollbar(table_frame, orient="vertical", command=tree.yview)
tree_scroll.pack(side="left", fill="y")
tree.configure(yscrollcommand=tree_scroll.set)

for i in range(21):
    tree.insert("", "end", text=str(i), values=(random, random.randint(0,1023), "00:00:00"))
    

#-Button to Start &Stop-#
root.update()
start_button=tk.Button(button_frame, text="Start", font=('calibri', 12), command=lambda: plot_start())
start_button.grid(row=6, column=0, pady=10)
root.update()
stop_button=tk.Button(button_frame, text="Stop", font=('calibri', 12),command=lambda: plot_stop())
stop_button.grid(row=6, column=1, pady=10)
#--Button to update delay time-#
update_delay_button=tk.Button(button_frame, text="Update Delay", command=update_delay_time)
update_delay_button.grid(row=2, column=1, pady=10)

#Entry for delay time#
delay_time_var=tk.StringVar()
delay_time_label=tk.Label(button_frame, text="TimeDelay", bg="pink")
delay_time_label.grid(row=0, column=1, pady=10)
delay_time_entry=tk.Entry(button_frame, textvariable=delay_time_var)
delay_time_entry.grid(row=1, column=1, pady=10)

#--Button to update scanning time-#
update_scan_button=tk.Button(button_frame, text="Update Scanning", command=update_scanning_time)
update_scan_button.grid(row=2, column=0, pady=10)

#Entry for scanning time#
scanning_time_var=tk.StringVar()
scanning_time_label=tk.Label(button_frame, text="Scanning Time(m)", bg="pink")
scanning_time_label.grid(row=0, column=0, pady=10)
scanning_time_entry=tk.Entry(button_frame, textvariable=scanning_time_var)
scanning_time_entry.grid(row=1, column=0, pady=10)

#-Button to connect serial port-#
connect_serial_button=tk.Button(button_frame, text="Connect Serial", command=connect_serial)
connect_serial_button.grid(row=5,column=0, columnspan=2,pady=10)

#Entry for Serial Port#
port_options=detect_serial_ports()
port_var=tk.StringVar(value=port_options[0])
port_label=tk.Label(button_frame, text="Serial Port", bg="pink")
port_label.grid(row=3, column=0, pady=10)
port_entry=tk.Entry(button_frame) 
#port_dropdown=tk.OptionMenu(port_entry, port_var, *port_options)
port_entry.grid(row=4, column=0, pady=10)

#port_entry=tk.OptionMenu(button_frame, port_var, *port_options)
#port_entry.grid(row=3, column=0, pady=10)

#-Button to print results-#
print_button=tk.Button(button_frame, text="Print Hasil", command=print_results)
print_button.grid(row=7, column=1, pady=10)
#-Button to exit application-#
exit_button=tk.Button(button_frame, text="Exit", command=exit_application)
exit_button.grid(row=8, column=0, columnspan=2, pady=10)
#-Button to Reset Settings-#
reset_button=tk.Button(button_frame, text="Reset Settings", command=reset_settings)
reset_button.grid(row=7, column=0, pady=10)

#add input fields and label for kernel Size
kernel_size_var=tk.StringVar(value="3")
kernel_size_label=tk.Label(button_frame, text="Kernel Size", bg="pink")
kernel_size_label.grid(row=3, column=1,pady=10)
kernel_size_entry=tk.Entry(button_frame, textvariable=kernel_size_var)
kernel_size_entry.grid(row=4, column=1, pady=10)
##-- Title---##
title_label=tk.Label(root, text="Fotodetektor UV", font=("Helvetica",24),bg="pink")
title_label.grid(row=0, column=1,sticky="n")

##--Footer Title--##
footer_label=tk.Label(root, text="Tim Lisin 2020", bg="pink")
footer_label.grid(row=2, column=1, sticky="s")

#root.after(1, plot_data)
root.mainloop()