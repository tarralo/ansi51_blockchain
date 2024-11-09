'''SHORT CIRCUIT ANALYSIS IN POWER SYSTEM WITH OPENDSS
REV 21 10 2024
SCRIPT MADE FOR RESULTS RETRIEVAL AND OVERCURRENT RELAY PARAMETERIZATION CURVES - IEEE 34 BUS'''

import py_dss_interface, time, winsound, math
import pandas as pd, numpy as np  
import matplotlib.pyplot as plt 
from mealpy import FloatVar, PSO, DE, GA, ARO
from concurrent.futures import ProcessPoolExecutor
from mpl_toolkits.axes_grid1.inset_locator import inset_axes

dss = py_dss_interface.DSS()
selected_curve = [0, 0.14, 13.5, 0.02] # IEC Standard Inverse curve
total_start = time.time()

'''MAIN FUNCTION'''
def main(): 
    system_34_bus = (r"models_and_results/ieee_34bus/ieee34Mod1.dss", 'IEEE34bus')
    simulated_sys = system_34_bus # Select the system to be analyzed
    sys_path = simulated_sys[0]  # Select the path of the system to be analyzed
    sys_name = simulated_sys[1]  # Select the name of the system to be analyzed
    nominal_df = get_dss(sys_path) # Get the nominal data from the selected system
    nominal_df.to_csv(f'nominal_df_{sys_name}.csv', encoding = 'utf-8-sig', header = True, sep = ';', decimal = ',', index=False) # save nominal nominal_df as csv
    relay_data = get_or_position(nominal_df) # Get the relay position using nominal data
    fault_data = fault_study(nominal_df, relay_data, sys_path) # Get the fault data using fault study
    relay_data = relay_config(nominal_df, relay_data, fault_data) # Make the relay parametrization
    tms_list = opt_relay_tms(relay_data.copy(), fault_data) # Optimize the relay tms
    relay_data['TMS'] = 0.0  # create a column for TMS
    for index, row in relay_data.iterrows(): # insert the optimized tms in the relay_data, for each relay Id
        id_index = int(row['Id'][1:]) - 1
        relay_data.loc[index, 'TMS'] = tms_list[id_index]
    relay_data.to_csv(f'relay_data_{sys_name}.csv', encoding = 'utf-8-sig', header = True, sep = ';', decimal = ',', index=False) # save relay_data as csv
    print('Total time:', time.time() - total_start, ' s ', (time.time() - total_start)/60, ' min') # print the total time of the script

'''GET DATA FROM OPENDSS'''
def get_dss(path): 
    dss.text(r'Clear') # Clear the DSS
    dss.text(f'Compile [{path}]') # Compile the system
    dss.circuit._pd_element_first()
    dss.text(rf'New EnergyMeter.dist element=[{dss.pdelements._name_read()}]') # Set the meter
    dss.text(r'Solve mode=snapshot') # Solve the system
    df = pd.DataFrame(columns=['Name', 'Phases', 'From', 'To', 'I_1', 'I_Angle_1', 'I_2', 'I_Angle_2', 'I_3', 'I_Angle_3', 
                                       'V_1', 'V_Angle_1', 'V_2', 'V_Angle_2', 'V_3', 'V_Angle_3']) # Create a DataFrame to store the data
    dss.pdelements.first() # Set the first element
    while True: 
        if 'Capacitor' not in dss.pdelements._name_read() and 'jumper' not in dss.pdelements._name_read() and 'sourcebus' not in dss.cktelement._bus_names()[0]:
            new_row = {'Name': None, 'Phases': None, 'From': None, 'To': None, 'I_1': 0, 'I_Angle_1': 0, 
                    'I_2': 0, 'I_Angle_2': 0, 'I_3': 0, 'I_Angle_3': 0, 
                    'V_1': 0, 'V_Angle_1': 0, 'V_2': 0, 'V_Angle_2': 0, 'V_3': 0, 'V_Angle_3': 0} # Create a new row
            new_row['Name'] = dss.pdelements._name_read() # Get the name of the element
            new_row['Phases'] = dss.cktelement._num_phases() # Get the number of phases of the element
            if dss.cktelement._num_phases() == 3 and len(dss.cktelement._bus_names()[0].split('.')) < 3: # If the element is a three phase element
                new_row['From'] = dss.cktelement._bus_names()[0] + '.1.2.3'
                new_row['To'] = dss.cktelement._bus_names()[1] + '.1.2.3'
            else: 
                new_row['From'] = dss.cktelement._bus_names()[0] # Get the name of the bus where the element start
                new_row['To'] = dss.cktelement._bus_names()[1] # Get the name of the bus where the element end
            if dss.cktelement._num_phases() == 1:
                nodes_from = dss.cktelement._bus_names()[0].split('.')[1]
                new_row[f'I_{nodes_from}'] = dss.cktelement._currents_mag_ang()[0]
                new_row[f'I_Angle_{nodes_from}'] = dss.cktelement._currents_mag_ang()[1]
                new_row[f'V_{nodes_from}'] = dss.cktelement._voltages_mag_ang()[0]
                new_row[f'V_Angle_{nodes_from}'] = dss.cktelement._voltages_mag_ang()[1]
            elif dss.cktelement._num_phases() == 2:
                nodes_from_1 = dss.cktelement._bus_names()[0].split('.')[1]
                nodes_from_2 = dss.cktelement._bus_names()[0].split('.')[2]
                new_row[f'I_{nodes_from_1}'] = dss.cktelement._currents_mag_ang()[0]
                new_row[f'I_Angle_{nodes_from_1}'] = dss.cktelement._currents_mag_ang()[1]
                new_row[f'I_{nodes_from_2}'] = dss.cktelement._currents_mag_ang()[2]
                new_row[f'I_Angle_{nodes_from_2}'] = dss.cktelement._currents_mag_ang()[3]
                new_row[f'V_{nodes_from_1}'] = dss.cktelement._voltages_mag_ang()[0]
                new_row[f'V_Angle_{nodes_from_1}'] = dss.cktelement._voltages_mag_ang()[1]
                new_row[f'V_{nodes_from_2}'] = dss.cktelement._voltages_mag_ang()[2]
                new_row[f'V_Angle_{nodes_from_2}'] = dss.cktelement._voltages_mag_ang()[3]
            elif dss.cktelement._num_phases() == 3:
                new_row['I_1'] = dss.cktelement._currents_mag_ang()[0]
                new_row['I_Angle_1'] = dss.cktelement._currents_mag_ang()[1]
                new_row['I_2'] = dss.cktelement._currents_mag_ang()[2]
                new_row['I_Angle_2'] = dss.cktelement._currents_mag_ang()[3]
                new_row['I_3'] = dss.cktelement._currents_mag_ang()[4]
                new_row['I_Angle_3'] = dss.cktelement._currents_mag_ang()[5]
                new_row['V_1'] = dss.cktelement._voltages_mag_ang()[0]
                new_row['V_Angle_1'] = dss.cktelement._voltages_mag_ang()[1]
                new_row['V_2'] = dss.cktelement._voltages_mag_ang()[2]
                new_row['V_Angle_2'] = dss.cktelement._voltages_mag_ang()[3]
                new_row['V_3'] = dss.cktelement._voltages_mag_ang()[4]
                new_row['V_Angle_3'] = dss.cktelement._voltages_mag_ang()[5]
            df.loc[len(df)] = new_row # Add the new row to the dataframe
        call_next = dss.pdelements._next() # Go to the next element
        if call_next == 0: break # If there is no more elements, break the loop
    return df
    
'''GET RELAY POSITION'''
def get_or_position(df):
    relay_data = pd.DataFrame(columns=['Id', 'Element', 'Bus', 'Phases', 'Dist'])
    for element in df['Name']: 
        new_row = {'Id': None, 'Element': None, 'Bus': None, 'Phases': None}
        new_row['Element'] = element # Get the name of the element where the relay is 
        new_row['Bus'] = [df[df['Name'] == element]['From'].values[0].split('.')[0], df[df['Name'] == element]['To'].values[0].split('.')[0]] # Get the bus where the relay is near 
        dss.circuit.set_active_bus(new_row['Bus'][0]) # Set the active bus
        new_row['Dist'] = dss.bus._distance() # Get the distance between the buses
        new_row['Phases'] = df[df['Name'] == element]['From'].values[0].split('.')[1:] # Get the phases of relay 
        relay_data.loc[len(relay_data)] = new_row # Add the new row to the dataframe
    relay_data = relay_data.sort_values(by='Dist', ascending=True, ignore_index=True) # Sort the dataframe by the distance between the buses
    count = 0
    for i in range(len(relay_data)):
        if '.reg' in relay_data['Element'][i] and i != 0 and '.reg' in relay_data['Element'][i - 1]: 
            relay_data.loc[i, 'Id'] = relay_data['Id'][i - 1]
        else: 
            relay_data.loc[i, 'Id'] = 'R' + str(count + 1)
            count += 1
    relay_data.drop(columns=['Dist'], inplace=True) # delete the 'Dist' column
    return relay_data

'''FAULT STUDY'''
def fault_study(df, relay_data, sys_path):
    fault_list = [] # Create a list to store the fault data
    for phases in range(1, 4): # 1, 2 and 3 phase faults
        fault_df = pd.DataFrame(columns=['Fault']) # Create a DataFrame to store the fault data
        fault_df['Fault'] = relay_data['Id'] # Add the relay id to the fault data
        fault_df.drop_duplicates(subset='Fault', keep='first', inplace=True, ignore_index=True) # Drop the duplicates
        for bus in relay_data['Bus']: fault_df[bus[1]] = 0.0 # Add the buses to the fault data
        for bus in fault_df.columns[1:]: 
            row = relay_data[relay_data['Bus'].apply(lambda x: x[1] == bus)] # Get the relay data of the bus
            if '.reg' in row['Element'].values[0]: ph = ['1', '2', '3'] # If the relay is in a regulator, the fault is a 3 phase fault
            else: ph = [str(i) for i in row['Phases'].values[0]] # Get the phases of the relay
            dss.text(r'Clear') # Clear the DSS
            dss.text(f'Compile [{sys_path}]') # Compile the system
            if phases == 1: # 1 phase fault
                dss.text(f'New Fault.test bus1={bus}.{'.'.join(ph[0])} phases={phases}') # 1 phase fault
                dss.text(r'Solve mode=snapshot') # Solve the system
                for element in relay_data['Element']: # Get the fault current of the relay
                    element_relay = relay_data[relay_data['Element'] == element]['Id'].values[0] # Get the relay id
                    row_index = fault_df[fault_df['Fault'] == element_relay].index[0] # Get the index of the relay
                    if '.reg' in element: # If the relay is in a regulator
                        i_nom = df[df['Name'] == element][f'I_{ph[0]}'].values[0] # Get the nominal current of the relay
                        element = element.split('.')[0] + f'.reg{ph[0]}' # Get the name of the relay
                        dss.circuit.set_active_element(element) # Set the active element
                        read_isc = dss.cktelement._currents_mag_ang()[0] # Get the fault current of the relay
                    else: 
                        dss.circuit.set_active_element(element) # Set the active element
                        if dss.cktelement._num_phases() == 3: # If the element is a three phase element
                            if ph[0] == '1': read_isc = dss.cktelement._currents_mag_ang()[0] # Get the fault current of the relay
                            elif ph[0] == '2': read_isc = dss.cktelement._currents_mag_ang()[2] # Get the fault current of the relay
                            else: read_isc = dss.cktelement._currents_mag_ang()[4] # Get the fault current of the relay
                        elif dss.cktelement._num_phases() == 2: read_isc = max(dss.cktelement._currents_mag_ang()[0], 
                                                                                 dss.cktelement._currents_mag_ang()[2]) # Get the fault current of the relay
                        else: read_isc = dss.cktelement._currents_mag_ang()[0] # Get the fault current of the relay
                        i_nom = max(df[df['Name'] == element][f'I_1'].values[0], df[df['Name'] == element][f'I_2'].values[0],
                                    df[df['Name'] == element][f'I_3'].values[0]) # Get the nominal current of the relay
                    if read_isc > 1.5 * i_nom and i_nom > 0: fault_df.loc[row_index, bus] = read_isc # If the fault current is greater than 1.5 times the nominal current, add the fault current to the fault data
            elif phases == 2 and len(ph) > 1: # 2 phase fault
                dss.text(f'New Fault.test bus1={bus}.{'.'.join(ph[:2])} phases={phases} ') # 2 phase fault
                dss.text(r'Solve mode=snapshot') # Solve the system
                count_reg = 0 # Create a counter to count the number of regulators
                prev_read = [0.0, 0.0, 0.0] # Create a list to store the fault current of the regulators
                for element in relay_data['Element']: # Get the fault current of the relay
                    element_relay = relay_data[relay_data['Element'] == element]['Id'].values[0] # Get the relay id
                    row_index = fault_df[fault_df['Fault'] == element_relay].index[0] # Get the index of the relay
                    if '.reg' in element: # If the relay is in a regulator
                        i_nom = df[df['Name'] == element][f'I_{count_reg + 1}'].values[0] # Get the nominal current of the relay
                        element = element.split('.')[0] + f'.reg{count_reg + 1}' # Get the name of the relay
                        dss.circuit.set_active_element(element) # Set the active element
                        read_isc = dss.cktelement._currents_mag_ang()[0] # Get the fault current of the relay
                        if read_isc > 1.5 * i_nom and i_nom > 0: # If the fault current is greater than 1.5 times the nominal current, add the fault current to the fault data
                            prev_read.append(read_isc) # Add the fault current to the list of fault currents
                            fault_df.loc[row_index, bus] = max(prev_read) # Add the fault current to the fault data
                        count_reg += 1 # Add 1 to the counter
                    else: # If the relay is not in a regulator
                        count_reg = 0 # Reset the counter
                        dss.circuit.set_active_element(element) # Set the active element
                        if dss.cktelement._num_phases() == 3: # If the element is a three phase element
                            if ph[0] == '1' and ph[1] == '2' or ph[0] == '2' and ph[1] == '1': # If the fault is between phases 1 and 2
                                read_isc = max(dss.cktelement._currents_mag_ang()[0], dss.cktelement._currents_mag_ang()[2]) # Get the fault current of the relay
                            elif ph[0] == '2' and ph[1] == '3' or ph[0] == '3' and ph[1] == '2': # If the fault is between phases 2 and 3
                                read_isc = max(dss.cktelement._currents_mag_ang()[2], dss.cktelement._currents_mag_ang()[4]) # Get the fault current of the relay
                            else: # If the fault is between phases 1 and 3
                                read_isc = max(dss.cktelement._currents_mag_ang()[0], dss.cktelement._currents_mag_ang()[4]) # Get the fault current of the relay
                        elif dss.cktelement._num_phases() == 2: read_isc = max(dss.cktelement._currents_mag_ang()[0],
                                                                                 dss.cktelement._currents_mag_ang()[2]) # Get the fault current of the relay
                        else: read_isc = dss.cktelement._currents_mag_ang()[0] # Get the fault current of the relay
                        i_nom = max(df[df['Name'] == element][f'I_1'].values[0], df[df['Name'] == element][f'I_2'].values[0],
                                    df[df['Name'] == element][f'I_3'].values[0]) # Get the nominal current of the relay
                        if read_isc > 1.5 * i_nom and i_nom > 0: fault_df.loc[row_index, bus] = read_isc # If the fault current is greater than 1.5 times the nominal current, add the fault current to the fault data
            elif phases == 3 and len(ph) > 2: # 3 phase fault
                dss.text(f'New Fault.test bus1={bus}.{'.'.join(ph[:3])} phases={phases} ') # 3 phase fault
                dss.text(r'Solve mode=snapshot') # Solve the system
                count_reg = 0 # Create a counter to count the number of regulators
                prev_read = [0.0, 0.0, 0.0] # Create a list to store the fault current of the regulators
                for element in relay_data['Element']: # Get the fault current of the relay
                    element_relay = relay_data[relay_data['Element'] == element]['Id'].values[0] # Get the relay id
                    row_index = fault_df[fault_df['Fault'] == element_relay].index[0] # Get the index of the relay
                    if '.reg' in element: # If the relay is in a regulator
                        i_nom = df[df['Name'] == element][f'I_{count_reg + 1}'].values[0] # Get the nominal current of the relay
                        element = element.split('.')[0] + f'.reg{count_reg + 1}' # Get the name of the relay
                        dss.circuit.set_active_element(element) # Set the active element
                        read_isc = dss.cktelement._currents_mag_ang()[0] # Get the fault current of the relay
                        if read_isc > 1.5 * i_nom and i_nom > 0: # If the fault current is greater than 1.5 times the nominal current, add the fault current to the fault data
                            prev_read.append(read_isc) # Add the fault current to the list of fault currents
                            fault_df.loc[row_index, bus] = max(prev_read) # Add the fault current to the fault data
                        count_reg += 1 # Add 1 to the counter
                    else: # If the relay is not in a regulator
                        count_reg = 0 # Reset the counter
                        dss.circuit.set_active_element(element) # Set the active element
                        if dss.cktelement._num_phases() == 3: # If the element is a three phase element
                            read_isc = max(dss.cktelement._currents_mag_ang()[0], dss.cktelement._currents_mag_ang()[2],
                                            dss.cktelement._currents_mag_ang()[4]) # Get the fault current of the relay
                        elif dss.cktelement._num_phases() == 2: read_isc = max(dss.cktelement._currents_mag_ang()[0],
                                                                                 dss.cktelement._currents_mag_ang()[2]) # Get the fault current of the relay
                        else: read_isc = dss.cktelement._currents_mag_ang()[0] # Get the fault current of the relay
                        i_nom = max(df[df['Name'] == element][f'I_1'].values[0], df[df['Name'] == element][f'I_2'].values[0],
                                    df[df['Name'] == element][f'I_3'].values[0])  # Get the nominal current of the relay
                        if read_isc > 1.5 * i_nom and i_nom > 0: fault_df.loc[row_index, bus] = read_isc # If the fault current is greater than 1.5 times the nominal current, add the fault current to the fault data
        fault_list.append(fault_df.copy()) # Add the fault data to the fault list
    for i in range(0,3): fault_list[i].to_csv(f'fault_{i + 1}ph.csv', encoding = 'utf-8-sig', header = True, 
                                                sep = ';', decimal = ',', index=False) # save fault data as csv 
    return fault_list
        
'''RELAY CONFIGURATION'''
def relay_config(df, relay_data, fault_data):
  rtc_list = (10/5, 15/5, 25/5, 40/5, 50/5, 75/5, 100/5, 150/5, 200/5, 
                300/5, 400/5, 600/5, 800/5, 1200/5, 3000/5, 4000/5) # commercial RTC values
  fs = 20 # ANSI security factor 
  relay_data['RTC'] = 0.0 # Create a column to store the RTC
  relay_data['Ip_ph(P)'] = 0.0 # Create a column to store the I pickup of phase (51F) in primary
  relay_data['Ip_ph(S)'] = 0.0 # Create a column to store the I pickup of neutral (51F) in secondary
  relay_data['Ip_n(P)'] = 0.0 # Create a column to store the I pickup of neutral (51N) in primary
  relay_data['Ip_n(S)'] = 0.0 # Create a column to store the I pickup of neutral (51N) in secondary
  relay_data['Isc_max(P)'] = 0.0 # Create a column to store the maximum fault current in primary
  relay_data['Isc_max(S)'] = 0.0 # Create a column to store the maximum fault current in secondary
  for relay in relay_data['Id']:
        # First: calculate current transformer ratio for each relay 
        for element in relay_data[relay_data['Id'] == relay]['Element'].values: 
            inom_max = 0
            for i in range(3): 
                current_value = df[df['Name'] == element][f'I_{i + 1}'].values[0]
                if current_value > inom_max: inom_max = current_value
        rtc_nom = min(rtc_list , key = lambda x:abs(x - inom_max/5)) # Get the RTC value
        max_isc = 0
        for i in range(3):
            row = fault_data[i][fault_data[i]['Fault'] == relay] # get the relay row in fault data
            fault_current = row.iloc[0, 1:].max() # get the maximum fault current in that row
            if fault_current > max_isc: max_isc = fault_current
        iprim_fault = max_isc / fs # Get the maximum fault current read in primary 
        rtc_fault = min(rtc_list , key = lambda x:abs(x - (iprim_fault/5))) # Get the near or equal value from rtc_list by division of the maximum fault current by 5 A
        relay_rtc = max(rtc_nom, rtc_fault) # Get the maximum value between rtc_nom and rtc_fault
        relay_data.loc[relay_data['Id'] == relay, 'RTC'] = relay_rtc # Get the maximum value between rtc_nom and rtc_fault
        relay_data.loc[relay_data['Id'] == relay, 'Isc_max(P)'] = max_isc # Get the maximum fault current in primary read by relay
        relay_data.loc[relay_data['Id'] == relay, 'Isc_max(S)'] = max_isc / relay_rtc # Get the maximum fault current in secondary read by relay
        # Second: calculate the pickup current of phase for each relay
        high_than = (inom_max * 1.5) / relay_rtc # i nominal times 1.5 (FC) divided by rtc
        # if the relay have only one phase 
        if len(relay_data[relay_data['Id'] == relay]['Phases'].values) == 1:
            less_than = fault_data[0][fault_data[0]['Fault'] == relay].iloc[0, 1:].max() / relay_rtc # get the value of isc in 1ph
        else: # if the relay is 2ph or 3ph
            less_than = fault_data[1][fault_data[1]['Fault'] == relay].iloc[0, 1:].max() / relay_rtc # get the value of isc in 2ph
        ipickup_ph = math.ceil(high_than * 2) / 2 # get the pickup current of phase
        if ipickup_ph == 0: ipickup_ph = 0.5
        while ipickup_ph >= less_than: # while the pickup current is greater than the fault current 
            ipickup_ph -= 0.5 # decrease the pickup current by 0.1
            if ipickup_ph <= 0.5: 
                ipickup_ph = 0.5
                break # if the pickup current is 0.5, break the loop
        relay_data.loc[relay_data['Id'] == relay, 'Ip_ph(P)'] = ipickup_ph * relay_rtc # get the pickup current of phase in primary
        relay_data.loc[relay_data['Id'] == relay, 'Ip_ph(S)'] = ipickup_ph # get the pickup current of phase in secondary
        # Third: calculate the pickup current of neutral for each relay
        high_than_n = inom_max * 0.1 / relay_rtc # i nominal times 0.1 (FD) divided by rtc
        less_than_n = fault_data[0][fault_data[0]['Fault'] == relay].iloc[0, 1:].max() / relay_rtc # get the value of isc in 1ph
        ipickup_n = math.ceil(high_than_n * 2) / 2 # get the pickup current of neutral
        if ipickup_n == 0: ipickup_n = 0.5 # if the pickup current is 0, set it to 0.5
        while ipickup_n >= less_than_n: # while the pickup current is greater than the fault current
            ipickup_n -= 0.5 # decrease the pickup current by 0.1
            if ipickup_n <= 0.5: 
                ipickup_n = 0.5
                break  # if the pickup current is 0.5, break the loop
        relay_data.loc[relay_data['Id'] == relay, 'Ip_n(P)'] = ipickup_n * relay_rtc # get the pickup current of neutral in primary
        relay_data.loc[relay_data['Id'] == relay, 'Ip_n(S)'] = ipickup_n # get the pickup current of neutral in secondary
        print('The relay parametrization of relay', relay, 'was successfully made!')
  return relay_data

'''OPTIMIZATION OF RELAY tms'''
def opt_relay_tms(relay_data, fault_data):
    cti = 0.2 # coordination time interval
    min_tms = 0.05 # minimum time dial setting
    nbus = len(fault_data[0].columns) - 1 # get the number of buses 
    nrelays = len(fault_data[0])  # get the number of relays
    pairs = np.zeros((len(relay_data), 2), dtype=int) # create a matrix to store the pairs of relay
    for i in range(len(relay_data)): # get the pairs of relay
        for j in range(len(relay_data)): # get the pairs of relay
            if relay_data['Bus'][i][0] == relay_data['Bus'][j][1] and relay_data['Id'][i] != relay_data['Id'][j]: # if the first bus of the relay is equal to the second bus of the relay
                pairs[i] = int(relay_data['Id'][i][1:]), int(relay_data['Id'][j][1:]) # get the pairs of relay
        second_position = relay_data['Bus'].apply(lambda x: x[1]) # get the second bus of the relay
        if relay_data['Bus'][i][0] not in second_position.values: pairs[i] = int(relay_data['Id'][i][1:]), 0 # if the first bus of the relay is not in all second buses of relay_data, the second position is 0
    pairs = np.unique(pairs, axis=0) # get the unique pairs of relay
    alpha = selected_curve[1] # get the alpha value
    beta = selected_curve[3] # get the beta value
    k_values = calculate_k(nbus, nrelays, fault_data, relay_data, alpha, beta) # calculate the k matrix
    tms_list = calc_tms(relay_data, pairs, k_values, cti, min_tms) # calculate the tms
    return tms_list

'''CALCULATE THE K'S VALUES'''
def calculate_k(nb, nr, fault, relay, a, b): 
    relay.drop_duplicates(subset='Id', keep='first', inplace=True, ignore_index=True) # exclude all rows in relay dataframe that have the same Id
    k_values = fault[0].copy(deep=True) # create a dataframe to store the k values
    # all the values after the first column are 0
    k_values.iloc[:, 1:] = 0
    for i in range(nr): # in range of rows = number of relays
        for j in range(nb): # in range of columns = number of buses
            if fault[0].iloc[i, j + 1] != 0:  # if the fault current is different from 0
                isc = fault[0].iloc[i, j + 1] # get the fault current
                ipickup = relay['Ip_ph(P)'][i] # get the pickup current of phase in primary
                k_values.iloc[i,j + 1] = a / (((isc / ipickup) ** b) - 1) # calculate the k value
    k_values.to_csv('k_values.csv', encoding = 'utf-8-sig', header = True, sep = ';', decimal = ',', index=False) # Save k_values as csv
    return k_values 

'''CALCULATE THE tms'''
def calc_tms(relay, pairs, k_values, cti, min_tms):
    global k_close_fault_g, nr_g, k_pairs_g
    global pairs_g, min_tms_g, cti_g
    min_tms_g = min_tms
    cti_g = cti
    # FIRST: get the k values of the closest fault
    relay.drop_duplicates(subset='Id', keep='first', inplace=True, ignore_index=True) # exclude all rows in relay dataframe that have the same Id
    nr = len(relay) # get the number of relays
    nr_g = nr
    nb = len(k_values.columns) - 1 # get the number of buses
    pairs_g = pairs
    k_close_fault = np.zeros(nr, dtype=float) # create a list to store the k values of the closest fault
    for i in range(nr): 
        for j in range(nb):
            # if the bus in k_values column is equal to the bus in position 1 of relay dataframe 'Bus' column
            if k_values.columns[j + 1] == relay['Bus'][i][1]: 
                k_close_fault[i] = k_values.iloc[i, j + 1] # get the k value of the closest fault 
                break # go to next relay
    k_close_fault_g = k_close_fault
    # save k_close_fault in txt file as k_i with i being the relay number, all in the same file
    with open('k_close_fault.txt', 'w') as f:
        for i in range(nr):
            f.write('R' + str(i + 1) + ' ' + str(k_close_fault[i]) + '\n')
    pairs = pairs[pairs[:,1] != 0] # get the pairs of relay that the second position is different from 0
    npairs = len(pairs) # get the number of pairs
    k_pairs = np.zeros((npairs, 2), dtype=float) # create a matrix to store the k values of the pairs of relay
    count = 0 # create a counter
    for pair in pairs:
        k_pairs[count, 0] = k_close_fault[pair[0] - 1] # get the k value of the first relay in the pair, so the principal relay
        k_pairs[count, 1] = k_values.iloc[pair[1] - 1, pair[0]] # get the k value of the second relay in the pair
        count += 1
    k_pairs_g = k_pairs
    # save k_pairs in txt file as k_i_j with i being the principal relay number and j being the secondary relay number, all in the same file
    with open('k_pairs.txt', 'w') as f:
        for i in range(npairs):
            f.write(str(pairs[i, 0]) + ' ' + str(pairs[i, 1]) + ' ' + str(k_pairs[i, 0]) + ' ' + str(k_pairs[i, 1]) + '\n')
    # SECOND: optimization of the tms, using mealpy library
    low_boundary = [min_tms] * nr # create a list with the minimum tms
    up_boundary = [1.2] * nr # create a list with the maximum tms
    # the bounds of all relays are the min_tms and 0.5 
    bounds = FloatVar(lb=low_boundary, ub=up_boundary) # create a list with the bounds of the tms
    problem_constrained = {
        'obj_func': objective_function, # the objective function
        'bounds': bounds, # the bounds of the tms
        'minmax': 'min', # the objective is to minimize the function
    }
    repetition = 24 # number of repetitions
    for iter in range(4):
        start = time.time()
        list_best_solution = []
        check_list = []
        solution_history = []
        time_history = []
        list_global_best_fit = []
        with ProcessPoolExecutor() as executor:
            results = list(executor.map(execute_iteration, [problem_constrained] * repetition,
                                        [k_close_fault] * repetition, [k_pairs] * repetition, [min_tms] * repetition, 
                                        [nr] * repetition, [pairs] * repetition, [cti] * repetition, [iter] * repetition))
            for model, iteration_time, check in results:
                check_list.append(check)
                list_best_solution.append(model.g_best.target.fitness)
                solution_history.append(model.g_best.solution)
                time_history.append(iteration_time)
                list_global_best_fit.append(model.history.list_global_best_fit)
        # Save data in a txt file 
        if iter == 0: 
            file_name = 'ARO'
            time_history_aro = time_history
            list_global_best_fit_aro = list_global_best_fit[np.argmin(list_best_solution)]
            list_epoch_time_aro = model.history.list_epoch_time
            tms_list = solution_history[np.argmin(list_best_solution)] 
        if iter == 1: 
            file_name = 'PSO'
            time_history_pso = time_history
            list_global_best_fit_pso = list_global_best_fit[np.argmin(list_best_solution)]
            list_epoch_time_pso = model.history.list_epoch_time
        if iter == 2: 
            file_name = 'DE'
            time_history_de = time_history
            list_global_best_fit_de = list_global_best_fit[np.argmin(list_best_solution)]
            list_epoch_time_de = model.history.list_epoch_time
        if iter == 3: 
            file_name = 'GA'
            time_history_ga = time_history
            list_global_best_fit_ga = list_global_best_fit[np.argmin(list_best_solution)]
            list_epoch_time_ga = model.history.list_epoch_time
        with open(f'simu_results{file_name}.txt', 'w') as f:
            f.write('fitness mean [s]: ' + str(np.mean(list_best_solution)) + '\n')
            f.write('fitness std [s]: ' + str(np.std(list_best_solution)) + '\n')
            f.write('fitness min [s]: ' + str(np.min(list_best_solution)) + '\n')
            f.write('time mean [s]: ' + str(np.mean(time_history)) + '\n')
            f.write('time std [s]: ' + str(np.std(time_history)) + '\n')
            f.write('time min [s]: ' + str(np.min(time_history)) + '\n')
            f.write('time max [s]: ' + str(np.max(time_history)) + '\n')
            f.write('total execution time [s]: ' + str(time.time() - start) + '\n')
            f.write('check: ' + str(check_list) + '\n')
    # Make a plot for comparission of the optimization algorithms: 1) plot for time history, 2) plot for fitness history, 3) plot for the epoch time
    plt.figure(figsize=(10, 5))
    x_axis = np.arange(1, repetition + 1, 1)
    plt.plot(x_axis, time_history_aro, linestyle = '-', linewidth = 2.0, label='ARO')
    plt.plot(x_axis, time_history_pso, linestyle = '--', linewidth = 1.8, label='PSO')
    plt.plot(x_axis, time_history_de, linestyle = '-.', linewidth = 1.6, label='DE')
    plt.plot(x_axis, time_history_ga, linestyle = ':', linewidth = 1.4, label='GA')
    plt.xlabel('Simulações')
    plt.ylabel('Tempo de simulação [s]')
    plt.legend(loc='best')
    plt.grid()
    plt.savefig('time_history.pdf')
    plt.figure(figsize=(10, 5))
    x_axis = np.arange(1, 1001, 1)
    plt.plot(x_axis, list_global_best_fit_aro, linestyle = '-', linewidth = 2.0, label='ARO')
    plt.plot(x_axis, list_global_best_fit_pso, linestyle = '--', linewidth = 1.8, label='PSO')
    plt.plot(x_axis, list_global_best_fit_de, linestyle = '-.', linewidth = 1.6, label='DE')
    plt.plot(x_axis, list_global_best_fit_ga, linestyle = ':', linewidth = 1.4, label='GA')
    plt.yscale('log')
    plt.xlabel('Iterações')
    plt.ylabel('Fitness [s]')
    plt.legend(loc='upper right')
    plt.grid(which='both', axis='both')
    # make a zoom for the last 100 iterations using inset axes
    axins = inset_axes(plt.gca(), width="50%", height="40%", loc='upper center')
    axins.plot(x_axis[899:1000], list_global_best_fit_aro[899:1000], linestyle = '-', linewidth = 2.0, label='ARO')
    axins.plot(x_axis[899:1000], list_global_best_fit_pso[899:1000], linestyle = '--', linewidth = 1.8, label='PSO')
    axins.plot(x_axis[899:1000], list_global_best_fit_de[899:1000], linestyle = '-.', linewidth = 1.6, label='DE')
    axins.plot(x_axis[899:1000], list_global_best_fit_ga[899:1000], linestyle = ':', linewidth = 1.4, label='GA')
    plt.grid()
    plt.savefig('fitness_history.pdf')
    plt.figure(figsize=(10, 5))
    plt.plot(x_axis, list_epoch_time_aro, linewidth = 2.0, label='ARO')
    plt.plot(x_axis, list_epoch_time_pso, linewidth = 1.8, label='PSO')
    plt.plot(x_axis, list_epoch_time_de, linewidth = 1.6, label='DE')
    plt.plot(x_axis, list_epoch_time_ga, linewidth = 1.4, label='GA')
    plt.xlabel('Iterações')
    plt.ylabel('Tempo [s]')
    plt.legend(loc='best')
    plt.grid()
    plt.savefig('epoch_time.pdf')
    for i in range(2): winsound.Beep((i + 1) * 1000, 1500) # make a alert sound when the optimization is finished
    return tms_list

def execute_iteration(problem_constrained, k_close_fault, k_pairs, min_tms, nr, pairs, cti, iter):
    global k_close_fault_g, k_pairs_g, min_tms_g, nr_g, pairs_g, cti_g
    k_close_fault_g = k_close_fault
    k_pairs_g = k_pairs
    min_tms_g = min_tms
    nr_g = nr
    pairs_g = pairs
    cti_g = cti
    iteration_start = time.time()
    if iter == 0: model = ARO.OriginalARO(epoch=1000, pop_size=500)
    if iter == 1: model = PSO.OriginalPSO(epoch=1000, pop_size=500)
    if iter == 2: model = DE.JADE(epoch=1000, pop_size=500)
    if iter == 3: model = GA.BaseGA(epoch=1000, pop_size=500)
    model.solve(problem=problem_constrained)
    iteration_time = time.time() - iteration_start
    return model, iteration_time, check_sol(model.g_best.solution)

'''CHECK CONSTRAINTS'''
def check_sol(solution):
    kp = k_pairs_g # get the k_pairs
    min_tms = min_tms_g # get the minimum tms
    nr = nr_g # get the number of relays
    pairs = pairs_g # get the pairs of relay
    cti = cti_g # get the coordination time interval
    pairs = pairs[pairs[:,1] != 0] # exclude from pairs the pairs that the second position is 0
    nc_pairs = len(kp) # get the number of constraints for pairs 
    g = np.zeros(nr + nc_pairs, dtype=float) # create a list to store the constraints
    for i in range(nr): g[i] = max(0, min_tms - solution[i]) 
    for i in range(nc_pairs): g[i + nr] = max(0, cti - ((kp[i, 1] * solution[pairs[i, 1] - 1]) - (kp[i, 0] * solution[pairs[i, 0] - 1])))
    return np.sum(g, axis=0)

'''OBJECTIVE FUNCTION'''
def objective_function(solution):
    # The function is for the i values in tms_list, will have the i value of k_close_fault multiplied by the candidate value
    kcf = k_close_fault_g # get the k_close_fault
    kp = k_pairs_g # get the k_pairs
    min_tms = min_tms_g # get the minimum tms
    nr = nr_g # get the number of relays
    pairs = pairs_g # get the pairs of relay
    cti = cti_g # get the coordination time interval
    k = 1 # power of the constraints, > 0
    coef_constraint = 100 # coefficient of the constraints
    pairs = pairs[pairs[:,1] != 0] # exclude from pairs the pairs that the second position is 0
    nc_pairs = len(kp) # get the number of constraints for pairs 
    # number_constraints = nr + nc_pairs # get the number of constraints
    g = np.zeros(nr + nc_pairs, dtype=float) # create a list to store the constraints
    for i in range(nr): g[i] = max(0, min_tms - solution[i]) 
    for i in range(nc_pairs): g[i + nr] = max(0, cti - ((kp[i, 1] * solution[pairs[i, 1] - 1]) - (kp[i, 0] * solution[pairs[i, 0] - 1])))
    return sum([kcf[i] * solution[i] for i in range(len(solution))]) + (np.sum(g**k, axis=0) * coef_constraint)

if __name__ == '__main__':
    main()
