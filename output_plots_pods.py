import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Function to parse the XML file and extract the SOC and speed data
# Function to parse the XML file and extract the SOC and speed data
def parse_xml(file_path):
    tree = ET.parse(file_path)
    root = tree.getroot()

    soc_data = {}
    speed_data = {}
    time_steps = []
    speed_data_1= {}
    soc_data_1 = {}

    for timestep in root.findall('timestep'):
        time = float(timestep.get('time'))
        if time > 3000:  # Filter data after timestep 3000
            time_steps.append(time)
            for vehicle in timestep.findall('vehicle'):
                vehicle_id = vehicle.get('id')
                if vehicle_id.startswith('f_1'):
                    actual_battery_capacity = float(vehicle.get('actualBatteryCapacity'))
                    maximum_battery_capacity = float(vehicle.get('maximumBatteryCapacity'))
                    speed = float(vehicle.get('speed'))
                    soc = (actual_battery_capacity / maximum_battery_capacity) * 100
                    if vehicle_id not in soc_data:
                        soc_data[vehicle_id] = {}
                    if vehicle_id not in speed_data:
                        speed_data[vehicle_id] = {}
                    soc_data[vehicle_id][time] = soc
                    speed_data[vehicle_id][time] = speed
                    if vehicle_id not in soc_data_1:
                        soc_data_1[vehicle_id] = []
                    if vehicle_id not in speed_data_1:
                        speed_data_1[vehicle_id] = []
                    soc_data_1[vehicle_id].append((time, soc))
                    speed_data_1[vehicle_id].append((time, speed))

    return soc_data,soc_data_1, speed_data, speed_data_1, sorted(time_steps)

# Function to align data to the same time steps
def align_data(data, time_steps):
    aligned_data = {}
    for vehicle_id, time_soc_map in data.items():
        aligned_soc = [time_soc_map.get(time, np.nan) for time in time_steps]
        aligned_data[vehicle_id] = aligned_soc
    return aligned_data

# Function to plot the SOC histogram
def plot_histogram(soc_data):
    all_soc_values = []
    for soc_list in soc_data.values():
        all_soc_values.extend(soc_list)

    plt.figure(figsize=(10, 6))
    plt.hist(all_soc_values, bins=50, color='blue', alpha=0.7)
    plt.xlabel('State of Charge (%)')
    plt.ylabel('Frequency')
    plt.title('Distribution of SOC Values')
    plt.axvline(x=10, color='red', linestyle='--', label='10% SOC')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


# # Function to plot the SOC box plot
# def plot_boxplot(soc_data):
#     soc_df = pd.DataFrame(soc_data)
#     plt.figure(figsize=(12, 6))
#     soc_df.boxplot()
#     plt.axhline(y=10, color='red', linestyle='--', label='10% SOC')
#     plt.xlabel('Vehicle ID')
#     plt.ylabel('State of Charge (%)')
#     plt.title('SOC Spread Across Vehicles')
#     plt.xticks(rotation=90)
#     plt.legend()
#     plt.tight_layout()
#     plt.show()
# Function to group data into 5-minute intervals
def group_data_by_interval(data, time_steps, interval=300):
    interval_data = {}
    interval_time_steps = []

    start_time = time_steps[0]
    end_time = time_steps[-1]
    current_interval = start_time

    while current_interval <= end_time:
        interval_end = current_interval + interval
        interval_label = f"{current_interval}-{interval_end}"
        interval_time_steps.append(interval_label)
        interval_data[interval_label] = []

        for vehicle_id, soc_values in data.items():
            interval_soc_values = [
                soc for soc, time in zip(soc_values, time_steps)
                if current_interval <= time < interval_end
            ]
            interval_data[interval_label].extend(interval_soc_values)

        current_interval = interval_end

    # Pad shorter lists with NaN to make sure all arrays have the same length
    max_length = max(len(values) for values in interval_data.values())
    for key in interval_data:
        interval_data[key] += [np.nan] * (max_length - len(interval_data[key]))

    return interval_data, interval_time_steps

# Function to plot the SOC box plot
def plot_boxplot(interval_data):
    soc_df = pd.DataFrame(interval_data)
    plt.figure(figsize=(12, 6))
    soc_df.boxplot()
    plt.axhline(y=10, color='red', linestyle='--', label='10% SOC')
    plt.xlabel('Time Interval (s)')
    plt.ylabel('State of Charge (%)')
    plt.title('SOC Spread Over Time Intervals')
    plt.xticks(rotation=90)
    plt.legend()
    plt.tight_layout()
    plt.show()
# Function to plot time series for vehicles with low SOC
def plot_low_soc_timeseries(soc_data, time_steps, threshold=10):
    plt.figure(figsize=(12, 6))
    for vehicle_id, soc_values in soc_data.items():
        if any(soc < threshold for soc in soc_values if not np.isnan(soc)):
            plt.plot(time_steps, soc_values, label=vehicle_id)

    plt.xlabel('Time (s)')
    plt.ylabel('State of Charge (%)')
    plt.title('SOC Over Time for Vehicles with Low SOC')
    plt.axhline(y=10, color='red', linestyle='--', label='10% SOC')
    #plt.legend()
    plt.tight_layout()
    plt.show()

def plot_statistics(data, time_steps, data_type='SOC'):
    values = np.full((len(time_steps), len(data)), np.nan)
    for i, time in enumerate(time_steps):
        for j, vehicle_id in enumerate(data.keys()):
            time_points = [point[0] for point in data[vehicle_id]]
            if time in time_points:
                data_index = time_points.index(time)
                values[i, j] = data[vehicle_id][data_index][1]

    data_df = pd.DataFrame(values, columns=data.keys(), index=time_steps)
    data_mean = data_df.mean(axis=1)
    data_median = data_df.median(axis=1)
    data_std = data_df.std(axis=1)

    plt.figure(figsize=(10, 6))
    plt.plot(time_steps, data_mean, label=f'Mean {data_type}', color='blue')
    plt.plot(time_steps, data_median, label=f'Median {data_type}', color='green')
    plt.fill_between(time_steps, data_mean - data_std, data_mean + data_std, color='blue', alpha=0.2, label='Standard Deviation')
    plt.xlabel('Time (s)')
    plt.ylabel(f'{data_type} (%)' if data_type == 'SOC' else f'{data_type} (m/s)')
    plt.title(f'{data_type} Statistics Over Time')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

def plot_statistics_agg(data, time_steps, interval=300, data_type='SOC'):
    interval_data, interval_time_steps = group_data_by_interval(data, time_steps, interval)

    data_df = pd.DataFrame(interval_data)
    data_mean = data_df.mean(axis=0)
    data_median = data_df.median(axis=0)
    data_std = data_df.std(axis=0)

    plt.figure(figsize=(10, 6))
    plt.plot(interval_time_steps, data_mean, label=f'Mean {data_type}', color='blue')
    plt.plot(interval_time_steps, data_median, label=f'Median {data_type}', color='green')
    plt.fill_between(interval_time_steps, data_mean - data_std, data_mean + data_std, color='blue', alpha=0.2, label='Standard Deviation')
    plt.xlabel('Time Interval (s)')
    plt.ylabel(f'{data_type} (%)' if data_type == 'SOC' else f'{data_type} (m/s)')
    plt.title(f'{data_type} Statistics Over Time')
    plt.xticks(rotation=90)
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


# Main function to execute the workflow
def main(file_path):
    soc_data, speed_data_1, speed_data, soc_data_1, time_steps = parse_xml(file_path)
    soc_data_aligned = align_data(soc_data, time_steps)
    speed_data_aligned = align_data(speed_data, time_steps)
    plot_histogram(soc_data_aligned)
    interval_data, interval_time_steps = group_data_by_interval(soc_data_aligned, time_steps, interval=300)
    plot_boxplot(interval_data)
    #plot_boxplot(soc_data_aligned)
    plot_low_soc_timeseries(soc_data_aligned, time_steps, threshold=10)
    # You can also plot statistics for speed if needed
    # plot_heatmap(speed_data, time_steps, data_type='Speed')
    #plot_statistics(speed_data_1, time_steps, data_type='Speed')
    #plot_statistics(soc_data_1, time_steps, data_type='SOC')
    plot_statistics_agg(speed_data_aligned, time_steps, interval=300, data_type='Speed')
    plot_statistics_agg(soc_data_aligned, time_steps, interval=300, data_type='SOC')

# Execute the main function with the path to the XML file
file_path = 'Battery.out.xml'
main(file_path)
# import xml.etree.ElementTree as ET
# import matplotlib.pyplot as plt
# import numpy as np
# import pandas as pd
#
# # Function to parse the XML file and extract the SOC and speed data
# def parse_xml(file_path):
#     tree = ET.parse(file_path)
#     root = tree.getroot()
#
#     soc_data = {}
#     speed_data = {}
#     time_steps = []
#     speed_data_1= {}
#     soc_data_1 = {}
#
#     for timestep in root.findall('timestep'):
#         time = float(timestep.get('time'))
#         if time > 3000:  # Filter data after timestep 3000
#             time_steps.append(time)
#             for vehicle in timestep.findall('vehicle'):
#                 vehicle_id = vehicle.get('id')
#                 if vehicle_id.startswith('f_1'):
#                     actual_battery_capacity = float(vehicle.get('actualBatteryCapacity'))
#                     maximum_battery_capacity = float(vehicle.get('maximumBatteryCapacity'))
#                     speed = float(vehicle.get('speed'))
#                     soc = (actual_battery_capacity / maximum_battery_capacity) * 100
#                     if vehicle_id not in soc_data:
#                         soc_data[vehicle_id] = {}
#                     if vehicle_id not in speed_data:
#                         speed_data[vehicle_id] = {}
#                     soc_data[vehicle_id][time] = soc
#                     speed_data[vehicle_id][time] = speed
#                     if vehicle_id not in soc_data_1:
#                         soc_data_1[vehicle_id] = []
#                     if vehicle_id not in speed_data_1:
#                         speed_data_1[vehicle_id] = []
#                     soc_data_1[vehicle_id].append((time, soc))
#                     speed_data_1[vehicle_id].append((time, speed))
#
#     return soc_data, speed_data, soc_data_1, speed_data_1, sorted(time_steps)
#
# # Function to align data to the same time steps
# def align_data(data, time_steps):
#     aligned_data = {}
#     for vehicle_id, time_soc_map in data.items():
#         aligned_soc = [time_soc_map.get(time, np.nan) for time in time_steps]
#         aligned_data[vehicle_id] = aligned_soc
#     return aligned_data
#
# # Function to plot the SOC histogram
# def plot_histogram(soc_data):
#     all_soc_values = []
#     for soc_list in soc_data.values():
#         all_soc_values.extend(soc_list)
#
#     plt.figure(figsize=(10, 6))
#     plt.hist(all_soc_values, bins=50, color='blue', alpha=0.7)
#     plt.xlabel('State of Charge (%)')
#     plt.ylabel('Frequency')
#     plt.title('Distribution of SOC Values (After Timestep 3000)')
#     plt.axvline(x=10, color='red', linestyle='--', label='10% SOC')
#     plt.legend()
#     plt.tight_layout()
#     plt.show()
# def group_data_by_interval(data, time_steps, interval=300):
#     interval_data = {}
#     interval_time_steps = []
#
#     start_time = time_steps[0]
#     end_time = time_steps[-1]
#     current_interval = start_time
#
#     while current_interval <= end_time:
#         interval_end = current_interval + interval
#         interval_label = f"{current_interval}-{interval_end}"
#         interval_time_steps.append(interval_label)
#         interval_data[interval_label] = []
#
#         for vehicle_id, soc_values in data.items():
#             interval_soc_values = [
#                 soc for soc, time in zip(soc_values, time_steps)
#                 if current_interval <= time < interval_end
#             ]
#             interval_data[interval_label].extend(interval_soc_values)
#
#         current_interval = interval_end
#
#     # Pad shorter lists with NaN to make sure all arrays have the same length
#     max_length = max(len(values) for values in interval_data.values())
#     for key in interval_data:
#         interval_data[key] += [np.nan] * (max_length - len(interval_data[key]))
#
#     return interval_data, interval_time_steps
#
# # Function to plot the SOC box plot
# def plot_boxplot(interval_data):
#     soc_df = pd.DataFrame(interval_data)
#     plt.figure(figsize=(12, 6))
#     soc_df.boxplot()
#     plt.axhline(y=10, color='red', linestyle='--', label='10% SOC')
#     plt.xlabel('Time Interval (s)')
#     plt.ylabel('State of Charge (%)')
#     plt.title('SOC Spread Over Time Intervals (After Timestep 3000)')
#     plt.xticks(rotation=90)
#     plt.legend()
#     plt.tight_layout()
#     plt.show()
#
#
#
# # Function to plot time series for vehicles with low SOC
# def plot_low_soc_timeseries(soc_data, time_steps, threshold=10):
#     plt.figure(figsize=(12, 6))
#     for vehicle_id, soc_values in soc_data.items():
#         if any(soc < threshold for soc in soc_values if not np.isnan(soc)):
#             plt.plot(time_steps, soc_values, label=vehicle_id)
#
#     plt.xlabel('Time (s)')
#     plt.ylabel('State of Charge (%)')
#     plt.title('SOC Over Time for Vehicles with Low SOC')
#     plt.axhline(y=10, color='red', linestyle='--', label='10% SOC')
#     #plt.legend()
#     plt.tight_layout()
#     plt.show()
#
# def plot_statistics(data, time_steps, data_type='SOC'):
#     values = np.full((len(time_steps), len(data)), np.nan)
#     for i, time in enumerate(time_steps):
#         for j, vehicle_id in enumerate(data.keys()):
#             time_points = [point[0] for point in data[vehicle_id]]
#             if time in time_points:
#                 data_index = time_points.index(time)
#                 values[i, j] = data[vehicle_id][data_index][1]
#
#     data_df = pd.DataFrame(values, columns=data.keys(), index=time_steps)
#     data_mean = data_df.mean(axis=1)
#     data_median = data_df.median(axis=1)
#     data_std = data_df.std(axis=1)
#
#     plt.figure(figsize=(10, 6))
#     plt.plot(time_steps, data_mean, label=f'Mean {data_type}', color='blue')
#     plt.plot(time_steps, data_median, label=f'Median {data_type}', color='green')
#     plt.fill_between(time_steps, data_mean - data_std, data_mean + data_std, color='blue', alpha=0.2, label='Standard Deviation')
#     plt.xlabel('Time (s)')
#     plt.ylabel(f'{data_type} (%)' if data_type == 'SOC' else f'{data_type} (m/s)')
#     plt.title(f'{data_type} Statistics Over Time')
#     plt.legend()
#     plt.tight_layout()
#     plt.show()
#
# # Main function to execute the workflow
# def main(file_path):
#     soc_data, speed_data, soc_data_1,speed_data_1, time_steps = parse_xml(file_path)
#     soc_data_aligned = align_data(soc_data, time_steps)
#     plot_histogram(soc_data_aligned)
#     interval_data, interval_time_steps = group_data_by_interval(soc_data_aligned, time_steps, interval=300)
#     plot_boxplot(interval_data)
#     #plot_boxplot(soc_data_aligned)
#     plot_low_soc_timeseries(soc_data_aligned, time_steps, threshold=10)
#     # You can also plot statistics for speed if needed
#     # plot_heatmap(speed_data, time_steps, data_type='Speed')
#     plot_statistics(soc_data_1, time_steps, data_type='SOC')
#     plot_statistics(speed_data_1, time_steps, data_type='Speed')
#
#
# # Execute the main function with the path to the XML file
# file_path = 'Battery.out.xml'
# main(file_path)