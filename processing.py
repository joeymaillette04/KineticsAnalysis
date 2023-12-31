# This file contains the code for processing the data from the accelerometer
# By: Joey Maillette and Karthigan Uthayan
# Date: 2023-11-15
# Prepared For: Charbel Azzi 
# Course: SYDE 182

import matplotlib.pyplot as plt
import pandas as pd
import csv
import math

# First recorded values of z-axis acceleration for cardboard and foam respectively
CARDBOARD_OFFSET = 0.486
FOAM_OFFSET = 0.522

class TimeInterval:
    # Constructor containing all of the properties of dynamics at a certain time
    def __init__(self, elapsed_time: float, accel: float, isFoam: bool):
        self.isFoam = isFoam # used for differences betwween foam and cardboard experiments
        self.elapsed_time = elapsed_time # raw elapsed time
        self.raw_acceleration = accel # raw acceleration in z-axis
        self.acceleration = 0.0 # acceleration with offset (calculated after)
        self.velocity_with_drift = 0.0 # velocity with drift (calculated after)
        self.velocity_no_drift = 0.0  # velocity without drift (calculated after)
        
        self.calculate_acceleration()

    # Calculate the acceleration with offset (3. Data Format)
    def calculate_acceleration(self):
        OFFSET = 0.0
        if self.isFoam:
            OFFSET = FOAM_OFFSET
        else:
            OFFSET = CARDBOARD_OFFSET

        self.acceleration = (self.raw_acceleration - OFFSET)*9.80665  

def calculate_avg_acceleration(time_intervals, t1, t2):
    count = 0
    summed_acceleration = 0.0
    for interval in time_intervals:
        if t1 <= interval.elapsed_time <= t2:
            count += 1
            summed_acceleration += interval.acceleration

    avg_acceleration = summed_acceleration / count if count != 0 else 0

    material = "Foam" if time_intervals[0].isFoam else "Cardboard"
    print(f"Average acceleration for {material} during the intial slide: {avg_acceleration:.3f} m/s^2")

    return avg_acceleration


# Calculate the velocity with drift (4. Continuous vs. Discrete Velocity)
def calculate_velocity_with_drift(time_intervals):
    for i in range(len(time_intervals)):

        for j in range(i):
            delta_t = 0.0
            # try except block to handle the first time interval
            try:
                delta_t = time_intervals[j].elapsed_time - time_intervals[j-1].elapsed_time # time difference between two time intervals
            except IndexError:
                delta_t = time_intervals[j].elapsed_time

            time_intervals[i].velocity_with_drift += time_intervals[j].acceleration*delta_t # Equation from 4.

# Calculate the velocity without drift (5. Velocity Drift Error)
def calculate_velocity_no_drift(time_intervals):
    # Case 1: Cardboard
    if (not time_intervals[0].isFoam):
        DRIFT_FACTOR = 0.072 # Visually determined slope (y2-y1/x2-x1 : for linear part of velocity with drift graph)
    
        for i in range(len(time_intervals)):
            time_intervals[i].velocity_no_drift = time_intervals[i].velocity_with_drift - DRIFT_FACTOR*time_intervals[i].elapsed_time # Equation from 5.
    
    # Case 2: Foam
    else:
        DRIFT_FACTOR_1 = 0.07625 # Visually Determined (for t=0 to t=5.339)
        DRIFT_FACTOR_2 = 0.01167 # Visually Determined (for t=7 to t=max)
        OFFSET_FIX = 0.2 # to account for the difference in y-values of the drift before and after the velocity

        # assume linear drift between intervals
        for interval in time_intervals:
            if (interval.elapsed_time <= 5.339):
                interval.velocity_no_drift = interval.velocity_with_drift - DRIFT_FACTOR_1*interval.elapsed_time # Equation from 5. (with first drift factor)
            elif (interval.elapsed_time >= 7.0):
                interval.velocity_no_drift = interval.velocity_with_drift - DRIFT_FACTOR_2*interval.elapsed_time -OFFSET_FIX # Equation from 5. (with second drift factor)
            
            # Due to a difference in the linear slope of the drift before and after movement, we need to linearly interpolate  
            # both the slope and the y-offset to account for the difference in the drift before and after movement
            else:
                DRIFT_FACTOR = DRIFT_FACTOR_1 + (DRIFT_FACTOR_2 - DRIFT_FACTOR_1)*(interval.elapsed_time - 5.339)/(7.0 - 5.339)
                OFFSET_FIX = (0.2)*(interval.elapsed_time - 5.339)/(7.0 - 5.339)
                interval.velocity_no_drift = interval.velocity_with_drift - DRIFT_FACTOR*interval.elapsed_time -OFFSET_FIX

# Calculate the peak velocities pre and post-impact
def calculate_peak_velocity(time_intervals, start_time, end_time):
    max_velocity = float('-inf') 
    min_velocity = float('inf')   

    for interval in time_intervals:
        if start_time <= interval.elapsed_time <= end_time:
            max_velocity = max(max_velocity, interval.velocity_no_drift)
            min_velocity = min(min_velocity, interval.velocity_no_drift)

    material = "Foam" if time_intervals[0].isFoam else "Cardboard"
    if max_velocity != float('-inf') and min_velocity != float('inf'):
        print(f"Maximum velocity for {material} post-impact: {max_velocity:.3f} m/s")
        print(f"Maximum velocity for {material} pre-impact: {min_velocity:.3f} m/s")
    else:
        print(f"No data for {material} in the specified time range")

    return max_velocity, min_velocity

# Calculate the experimental work, friction force, and coefficient of friction
def calculate_exp_friction(time_intervals):
    vel_final = 2.105 if time_intervals[0].isFoam else 2.157  # from peak velocity calculations
    work = (0.5 * 1.88 * vel_final ** 2) - (1.88 * 9.80665 * 0.295)
    friction_force = abs(work / 0.59)
    friction_coeff = abs(friction_force / (1.88 * 9.80665 * math.cos(math.pi / 6)))

    material = "Foam" if time_intervals[0].isFoam else "Cardboard"
    print(f"Experimental Friction Calculations for {material}:")
    print(f"  Work Done: {work:.3f} Joules")
    print(f"  Friction Force: {friction_force:.3f} Newtons")
    print(f"  Friction Coefficient: {friction_coeff:.3f}\n")

    return work, friction_force, friction_coeff


# Plotting the acceleration vs. time graph from list of time intervals
def plot_acceleration(time_intervals, fixedAccel: bool):
    if not time_intervals:  # Check if the list is empty
        print("No data available for plotting acceleration.")
        return

    times = [interval.elapsed_time for interval in time_intervals]
    accelerations = [interval.raw_acceleration if not fixedAccel else interval.acceleration for interval in time_intervals]

    material = "Foam" if time_intervals[0].isFoam else "Cardboard"
    title = f"{'Raw Acceleration' if not fixedAccel else 'Acceleration with Offset'} vs. Time ({material})"

    plt.figure(figsize=(10, 6))
    plt.plot(times, accelerations, marker='o', markersize=2)
    plt.title(title)
    plt.xlabel('Elapsed Time (s)')
    plt.ylabel('Acceleration (m/s^2)' if not fixedAccel else 'Corrected Acceleration (m/s^2)')
    plt.grid(True)
    plt.show()


# Plotting the velocity vs. time graph from list of time intervals
def plot_velocity(time_intervals, fixedVel: bool):
    if not time_intervals:  # Check if the list is empty
        print("No data available for plotting velocity.")
        return

    times = [interval.elapsed_time for interval in time_intervals]
    velocities = [interval.velocity_with_drift if not fixedVel else interval.velocity_no_drift for interval in time_intervals]

    material = "Foam" if time_intervals[0].isFoam else "Cardboard"
    title = f"Velocity {'with Drift' if not fixedVel else 'without Drift'} vs. Time ({material})"

    plt.figure(figsize=(10, 6))
    plt.plot(times, velocities, marker='o', markersize=2)
    plt.title(title)
    plt.xlabel('Elapsed Time (s)')
    plt.ylabel('Velocity (m/s)')
    plt.grid(True)
    plt.show()

# Helper function to create a list of TimeInterval objects from a dataframe
def create_time_intervals(dataframe, isFoam: bool):
    time_intervals = []
    for _, row in dataframe.iterrows():
        elapsed_time = row["elapsed (s)"]
        acceleration = row["z-axis (g)"]
        time_interval = TimeInterval(elapsed_time, acceleration, isFoam)
        time_intervals.append(time_interval)
    return time_intervals

# Helper function to read from CSV files
def read_csv_data(filename):
    try:
        data = pd.read_csv(filename)
        return data
    except FileNotFoundError:
        print(f"File {filename} not found.")
        return None
    
# Helper function to write the results to a CSV file
def write_results_to_csv(time_intervals, filename):
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        # Writing the header
        writer.writerow(['Elapsed Time (s)', 'Velocity No Drift (m/s)'])
        # Writing the data rows
        for interval in time_intervals:
            writer.writerow([interval.elapsed_time, interval.velocity_no_drift])

# Reading the CSV files
cardboard_data = read_csv_data("Cardboard Data.csv")
foam_data = read_csv_data("Foam Data.csv")

# Creating the time interval lists
cardboard_intervals = create_time_intervals(cardboard_data, False) if cardboard_data is not None else []
foam_intervals = create_time_intervals(foam_data, True) if foam_data is not None else []


####################################### PLOTS #########################################
# Plots of no-offset accel vs. time
plot_acceleration(cardboard_intervals, False)
plot_acceleration(foam_intervals, False)

# Plots of offset accel vs. time
plot_acceleration(cardboard_intervals, True)
plot_acceleration(foam_intervals, True)

# Calculating the velocities from acceleration
calculate_velocity_with_drift(cardboard_intervals)
calculate_velocity_with_drift(foam_intervals)

# Calculating the velocities without drift
calculate_velocity_no_drift(cardboard_intervals)
calculate_velocity_no_drift(foam_intervals)

# Plots of velocity (with drift) vs. time
plot_velocity(cardboard_intervals, False)
plot_velocity(foam_intervals, False)

# Plots of velocity (without drift) vs. time
plot_velocity(cardboard_intervals, True)
plot_velocity(foam_intervals, True)

####################################### VALUES #########################################
print("RESULTS:\n")
calculate_avg_acceleration(cardboard_intervals, 5.4, 5.934)
calculate_avg_acceleration(foam_intervals, 5.339, 5.878)
print()
calculate_peak_velocity(cardboard_intervals, 5.302, 6.1)
calculate_peak_velocity(foam_intervals, 5.339, 6.1)
print()
calculate_exp_friction(cardboard_intervals)
calculate_exp_friction(foam_intervals)
print()

####################################### WRITE TO CSV #########################################
write_results_to_csv(cardboard_intervals, "Cardboard_Results.csv")
write_results_to_csv(foam_intervals, "Foam_Results.csv")