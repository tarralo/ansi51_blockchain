'''PLOT THE RELAY CURVE AND STORE THE DATA IN A BLOCKCHAIN LEDGER - STREAMLIT APP'''

import streamlit as st, numpy as np, pandas as pd, plotly.graph_objects as go
import ast, hashlib, datetime as datetime, time 
from dataclasses import dataclass
from typing import Any, List
from PIL import Image

# First - Record Data Class
# Create a record data class that consists of the 'sender' (user), 'receiver' (relay) and 'transaction' (relay data)
@dataclass
class Record: 
    sender: str # user
    receiver: str # pair of relays
    transaction: str # relay data

# Second - Modify the Existing Block Data Class to Store the Record Data
@dataclass 
class Block: 
    record: Record # record of the hash or block
    creator_id: int # creator ID
    prev_hash: str = 0 # previous hash
    timestamp: str = datetime.datetime.now().strftime('%d-%m-%Y %H:%M:%S') # time of the block creation in UTC format
    nonce: str = 0 # number added to hash or block as a proof of work
    # Function to hash the block
    def hash_block(self): 
        cript = hashlib.sha256() # create a hash object -> verificar se há diferença entre os tipos disponíveis: 512, 244...
        record = str(self.record).encode() # encode the record
        cript.update(record) # update the hash object with the record
        creator_id = str(self.creator_id).encode() # encode the creator ID
        cript.update(creator_id) # update the hash object with the creator ID
        timestamp = str(self.timestamp).encode() # encode the timestamp
        cript.update(timestamp) # update the hash object with the timestamp
        prev_hash = str(self.prev_hash).encode() # encode the previous hash
        cript.update(prev_hash) # update the hash object with the previous hash
        nonce = str(self.nonce).encode() # encode the nonce
        cript.update(nonce) # update the hash object with the nonce
        return cript.hexdigest() # return the hexadecimal digest of the hash object

# Third - Modify the Existing Blockchain Data Class to Store the Block Data
@dataclass
class Blockchain: 
    chain: List[Block] # chain of blocks
    difficulty: int = 2 # initial difficulty of the proof of work
    # Function to proof of work
    def pow(self, block): 
        calc_hash = block.hash_block() # calculate the hash of the block
        n_zeros = "0" * self.difficulty # create a string with n_zeros
        while not calc_hash.startswith(n_zeros):
            block.nonce += 1 # increment the nonce
            calc_hash = block.hash_block() # calculate the hash of the block
        return block # return the block
    # Function to add a block to the chain
    def addblock(self, candidate_block):
        block = self.pow(candidate_block) # proof of work
        if block.hash_block().startswith("0" * self.difficulty):
            self.chain.append(block) # add the block to the chain
            return True # sign of success
        else: 
            st.toast("Block Rejected!!") # print the message
            return False # sign of failure
    # Function to validate the chain
    def validate(self):
        block_h = self.chain[0].hash_block() # get the hash of the first block
        block_timestamp = self.chain[0].timestamp # get the timestamp of the first block
        for block in self.chain[1:]:
            if block_h != block.prev_hash: 
                st.toast("Invalid Blockhain") # print the message
                return False
            block_h = block.hash_block() # get the hash of the block
            if block_timestamp > block.timestamp: # Check if the timestamp is in the correct order
                st.toast("Invalid Blockhain") # print the message
                return False
        return True

# Fourth - Setup for streamlit
@st.cache_resource(experimental_allow_widgets=True)
def setup(): return Blockchain([Block("Genesis", 0)])
    
# Fifth - Main Function
def main():
    check = False # check if the block was mined
    blockchain = setup()
    col1, col2 = st.columns((2,1))
    col1.markdown("<span style='font-size: 22px;'><strong>:rainbow[ANSI 51 Plotter App] ⚡ + :rainbow[Blockchain Ledger] 🔗</strong></span>", unsafe_allow_html=True)
    # col1.markdown('**:rainbow[ANSI 51 Plotter App]** ⚡ + **:rainbow[Blockchain Ledger]** 🔗')
    with col1.popover('**Made by** Luiz A. Tarralo Passatuto'):
        st.write('**Email** tarralo@ufu.br') 
        st.markdown('[GitHub](https://github.com/tarralo)')
        st.markdown('[Google Scholar](https://scholar.google.com/citations?hl=pt-BR&user=T3-3ZmYAAAAJ)') 
        st.markdown('[Lattes](http://lattes.cnpq.br/3731667622661237)')
        st.markdown('[ResearchGate](https://www.researchgate.net/profile/Luiz-Tarralo-Passatuto)')
    with col1.popover('**Guided by** Wellington Maycon S. Bernardes'):
        st.write('**Email** wmsbernardes@ufu.br')
        st.markdown('[GitHub](https://github.com/wmsb)')
        st.markdown('[Google Scholar](https://scholar.google.com.br/citations?user=6mtTof0AAAAJ&hl=pt-BR)')
        st.markdown('[ORCID](https://orcid.org/0000-0001-7401-3478)')
        st.markdown('[Lattes](http://lattes.cnpq.br/8631549983581675)')
        st.markdown('[ResearchGate](https://www.researchgate.net/profile/Wellington-Maycon-S-Bernardes)')
    col1.markdown('[GitHub Repository](https://github.com/tarralo/ansi51_blockchain)')
    col1.write('**Last Update** 08 November 2024')
    leapse_logo = Image.open(r"leapse.png")
    col2.image(leapse_logo, use_column_width='auto') 
    with col2.popover("**:green[Laboratory of Alternative Energies and Protection of Electrical Systems]**"):
        st.write('**Uberlândia, Brazil**')
        st.markdown('[LinkedIn](https://www.linkedin.com/company/leapse-ufu/)')
        st.markdown('[Instagram](https://www.instagram.com/leapse.ufu/)')
    with st.popover("Supported by 👨‍🏫"):
        pop_col1, pop_col2, pop_col3 = st.columns(3, gap="large")
        capes_logo = Image.open(r"streamcloud_app/capes.png")
        pop_col1.image(capes_logo, caption = "CAPES - Coordination for the Improvement of Higher Education Personnel", width=200)
        ufu_logo = Image.open(r"ufu.png")
        pop_col2.image(ufu_logo, caption = "UFU - Federal University of Uberlândia", width=200)
        ppgeelt_logo = Image.open(r"ppgeelt.png")
        pop_col3.image(ppgeelt_logo, caption = "PPGEELT - Post-Graduation Electrical Engineering Program", width=200) 
    uploaded_file = st.file_uploader('Choose a .csv file with relay data', accept_multiple_files=False, type='csv') # the user insert the .csv file with the relay data
    if uploaded_file is not None:
        try: relay_data = pd.read_csv(uploaded_file, encoding='utf-8', sep=';', decimal=',') # read the .csv file
        except Exception as e: st.write('Error: ', e) # if there is an error, show the error
        pairs = get_pairs(relay_data).tolist() # get the pairs of relay
        sender = st.text_input('Sender ⬆️') # the user insert his name
        if sender is not None: selected_pair = st.selectbox('Select the relay pair ⬇️', pairs) # Make a select box to choose the relay pair
        if selected_pair is not None:
            receiver = 'R' + str(selected_pair[0]) + ' - R' + str(selected_pair[1])
            prim_relay = relay_data[relay_data['Id'] == ('R' + str(selected_pair[0]))]
            prim_pickup = prim_relay['Ip_ph(P)'].values[0]
            prim_tms = prim_relay['TMS'].values[0]
            prim_isc = prim_relay['Isc_max(P)'].values[0]
            sec_relay = relay_data[relay_data['Id'] == ('R' + str(selected_pair[1]))]
            sec_pickup = sec_relay['Ip_ph(P)'].values[0]
            sec_tms = sec_relay['TMS'].values[0]
            sec_isc = sec_relay['Isc_max(P)'].values[0]
            transaction_to_relay = f'Primary Pickup: {prim_pickup} A, Primary TMS: {prim_tms} s, Secondary Pickup: {sec_pickup} A, Secondary TMS: {sec_tms} s'
            current_step = st.number_input('Insert a step for the current curve 📏', 0.01, 10.0, 0.01) # the user insert the current multiplier
            if st.button('Mine Block'):
                start_time = time.time() # start the time
                prev_block = blockchain.chain[-1] # get the last block in the chain
                prev_block_hash = prev_block.hash_block() # get the hash of the last block
                new_block = Block(
                    record = Record(sender, receiver, transaction_to_relay),
                    creator_id = 1,
                    prev_hash = prev_block_hash) # create a new block
                check = blockchain.addblock(new_block) # add the new block to the chain
            if check:
                current_values = np.arange(1, 1000 + current_step, current_step) # current values for primary relay plot
                time_prim = time_plot(prim_tms, current_values) # calculate the time for primary relay
                time_sec = time_plot(sec_tms, current_values) # calculate the time for secondary relay
                # Make the plot for primary relay and secondary relay in the same figure
                if time_prim is not None and time_sec is not None:
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=current_values, y=time_prim, marker=dict(color='darkcyan'), name='Primary Relay'))
                    fig.add_trace(go.Scatter(x=current_values, y=time_sec, marker=dict(color='crimson'), name='Secondary Relay'))
                    fig.update_xaxes(type='log', title='Pickup Multiplier', showgrid=True, minor=dict(showgrid=True))
                    fig.update_yaxes(type='log', title='Time (s)', showgrid=True, minor=dict(showgrid=True))
                    fig.update_layout(
                        title='ANSI 51 Overcurrent Relay Time Curve',
                        width=800,
                        height=500,
                        margin=dict(l=50, r=50, t= 50, b=50)
                    )
                    # put a point in the curve that represents the Isc_max(P) value for each relay and respective time
                    time_isc_prim = time_plot(prim_tms, [prim_isc / prim_pickup]) # calculate the time for primary relay closest Isc
                    time_isc_sec = time_plot(sec_tms, [sec_isc / sec_pickup]) # calculate the time for secondary relay closest Isc
                    fig.add_trace(go.Scatter(x=[prim_isc / prim_pickup], y=[time_isc_prim[0]], mode='markers', marker=dict(color='black', symbol='diamond', size=8), name='Primary Relay Closest Isc'))
                    fig.add_trace(go.Scatter(x=[sec_isc / sec_pickup], y=[time_isc_sec[0]], mode='markers', marker=dict(color='darkviolet', symbol='diamond', size=8), name='Secondary Relay Closest Isc'))
                    # put the value of prim_isc and time_isc_prim above the point in the plot
                    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(color='black'), name=f'Isc Prim: {round((prim_isc/1000),4)} kA, Time: {round(time_isc_prim[0],4)} s'))
                    fig.add_trace(go.Scatter(x=[None], y=[None], mode='markers', marker=dict(color='darkviolet'), name=f'Isc Sec: {round((sec_isc/1000),4)} kA, Time: {round(time_isc_sec[0],4)} s'))
                    st.plotly_chart(fig, use_container_width=False) # show the plot
                    st.write(":green[_Block Mined Successfully_] ⛏️") # print the message
                    st.write(f"**In** :blue[{new_block.nonce}] **attempts and** :red[{time.time() - start_time:.4f}] **seconds**") # print the number of attempts and the time 

    st.markdown(":violet[**Blockchain Ledger**] 📓")
    blockchain_df = pd.DataFrame(blockchain.chain)
    st.write(blockchain_df)
    if st.button("Clear Ledger"):
        blockchain.chain = [Block("Genesis", 0)]
        st.rerun() # reload the page
        st.toast("Ledger Cleared", icon="🧹")
    difficulty = st.slider(':orange[**Difficulty**] 💪', 1, 10, 2)
    blockchain.difficulty = difficulty    
    st.sidebar.markdown("**:red-background[:red[Block Info]]** 🧱")
    select_block_to_inspect = st.sidebar.selectbox('Select a block to inspect', blockchain.chain)
    st.sidebar.write(select_block_to_inspect)
    if st.button("Validate Blockchain"): st.write(blockchain.validate())
    st.download_button(label='Download Json', data=blockchain_df.to_json(orient='records'), file_name='blockchain.json', mime='application/json')

# Function to calculate the time for the relay curve
def time_plot(tms, current_values):
    alpha = 0.14
    beta = 0.02
    time = np.zeros(len(current_values), dtype=float)
    for i in range(len(current_values)):
        mult_current = current_values[i]
        if mult_current <= 1: time[i] = None 
        else: time[i] = tms * (alpha / ((mult_current**beta) - 1))
    return time

# Function to get the pairs of relay
def get_pairs(relay_data):
    pairs = np.zeros((len(relay_data), 2), dtype=int) # create a matrix to store the pairs of relay
    relay_data['Bus'] = relay_data['Bus'].apply(lambda x: ast.literal_eval(x)) # get only the numbers in 'Bus' column and convert to int
    for i in range(len(relay_data)): # get the pairs of relay
        for j in range(len(relay_data)): # get the pairs of relay
            if relay_data['Bus'][i][0] == relay_data['Bus'][j][1] and relay_data['Id'][i] != relay_data['Id'][j]: # if the first bus of the relay is equal to the second bus of the relay
                pairs[i] = int(relay_data['Id'][i][1:]), int(relay_data['Id'][j][1:]) # get the pairs of relay
        second_position = relay_data['Bus'].apply(lambda x: x[1]) # get the second bus of the relay
        if relay_data['Bus'][i][0] not in second_position.values: pairs[i] = int(relay_data['Id'][i][1:]), 0 # if the first bus of the relay is not in all second buses of relay_data, the second position is 0
    pairs = np.unique(pairs, axis=0) # get the unique pairs of relay
    return pairs[pairs[:,1] != 0]

if __name__ == '__main__':
    main()
    


