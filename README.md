## ansi51_blockchain  - Relay Processing / Optimization using ARO and Blockchain App

This repository contains the research results from the Laboratory of Alternative Energies and Electrical System Protection, conducted by Eng. Luiz A. Tarralo Passatuto ([tarralo](https://github.com/tarralo)) under the guidance of Prof. Phd. Wellington Maycon S. Bernardes ([wmsb](https://github.com/wmsb)). This study contributes for fault analysis using [**OpenDSS**](https://www.epri.com/pages/sa/opendss) , optimal parameters for overcurrent relay via [**Artificial Rabbit Optimization**](https://seyedalimirjalili.com/aro) metaheuristic and processing data via **Blockchain**. The content here is the result of the Master’s Dissertation work of Luiz A. Tarralo Passatuto and is available for various uses, provided that the original work and its authors are credited.

## Published Papers 

> Inserir referência do artigo do CBRED assim que a tiver

> Inserir referência da Dissertação assim que a tiver

## Relay Configuration ('ARO_optimization_....py')
This script is responsible for configuring the settings of overcurrent relays in an electrical protection system based on fault data  and current values from the system (via [**py-dss-interface**](https://pypi.org/project/py-dss-interface/)). The main parameters computed include:

- **RTC (Relay Time-Current)**: This is determined by comparing the maximum current values obtained for each relay, considering a predefined list of commercial RTC values and fault data.
- **Pickup Current for Phase and Neutral**: The pickup current for both phase and neutral is calculated for each relay by comparing fault currents with nominal current values. The value is adjusted to ensure reliable protection.
- **Maximum Fault Current**: The maximum fault current for each relay is computed in both primary and secondary systems.
- **Pairing Relays**: relays are paired based on their bus connections.
- **K-values Calculation**: values calculated for each relay and each pair, which are used in the coordination process and optimization.
- **TMS Calculation**: the time parameter is optimized to minimize operational time in seconds for all relays in power system while ensuring reliable protection.
  
The optimization was made via **ARO**, but other four metaheuristics will run for efficiency comparision. The script made use of paralel processing build-in package from Python for better performance. In this repository readers can find models and results for three IEEE radial test networks: 13-bus (models_and_results/ieee_13bus), 34-bus (models_and_results/ieee_34bu)s and 37-bus (models_and_results/ieee_37bus), for examples with and without DERs connected. There are options for comparission between four metaheuristic using [**mealpy**](https://mealpy.readthedocs.io/en/latest/) 

## Streamcloud Application (Visit the [main_app](https://ansi51blockchain.streamlit.app/))

This interactive web application allows users to explore the behavior of overcurrent relay protection systems by plotting ANSI 51 time-current characteristic curves while simultaneously recording relay data in a Blockchain ledger. Developed using Streamlit, the app enables users to input relay data from a `.csv` file and visualize the coordination between primary and secondary relays.

The application employs a custom-built Blockchain structure to simulate the secure recording of relay data transactions. Users can interact with the app by selecting relay pairs, adjusting current multipliers, and mining blocks, which are then added to the Blockchain ledger after completing a proof-of-work algorithm.

## Features
- **Relay Data Visualization:** Plot the ANSI 51 characteristic curves for primary and secondary relays, based on input data from `.csv` files.
- **Blockchain Integration:** Transaction data (e.g., relay settings) is securely stored and validated in a Blockchain ledger.
- **Relay Pair Coordination:** Users can input relay data and visualize the coordination between two relays, including the time-current curve and specific relay settings such as pickup current (Ip) and time multiplier (TMS).
- **Proof of Work (Mining):** Blocks are mined to add transactions to the Blockchain, demonstrating the app's commitment to decentralized record-keeping.
- **Isc Max Calculation:** Plot the time corresponding to the maximum short-circuit current (Isc_max) for each relay and its time delay.

- ## Technical Details
1. **Blockchain Architecture:**
   - The app utilizes a basic Blockchain structure with blocks containing transaction data and a proof-of-work mechanism for block validation.
   - Each block includes a record with the sender, receiver (relay pair), and transaction details such as primary and secondary relay settings.
   - Blocks are linked together via hashes, ensuring the integrity and immutability of the data.

2. **Data Flow:**
   - Users upload a `.csv` file containing relay data, and select relay pairs to visualize their coordination.
   - The app calculates and plots the ANSI 51 curves for primary and secondary relays, allowing users to adjust the current multiplier to see real-time changes.
   - Relay data is mined into the Blockchain with each interaction, creating a transparent and secure ledger of user inputs and relay settings.

3. **Proof of Work:**
   - The app employs a simple proof-of-work algorithm, requiring users to "mine" a block by solving a hash puzzle with **nonce**. The block is only added to the Blockchain once a valid solution is found.
   - The difficulty of the mining process can be adjusted, providing a hands-on understanding of the blockchain's computational requirements.
  
Further information can be found in the original work (link to be made available soon).

## Acknowledgements 

This work was supported by the Fundação de Amparo à Pesquisa do Estado de Minas Gerais (FAPEMIG) under the Demanda Universal program (APQ-02176-22), the Coordenação de Aperfeiçoamento de Pessoal de Nível Superior - Brazil (CAPES) under the Funding Code 001, and the Postgraduate Program in Electrical Engineering (PPGEELT) at the Faculty of Electrical Engineering, Federal University of Uberlândia. We would like to express my sincere gratitude to these institutions for their invaluable support throughout the development of this research.

## Screenshots

<p align="center">
<img src="https://github.com/tarralo/ansi51_blockchain/blob/bcbd45feefec24719c2d26f1533469a6b7b77ac5/models_and_results/app_tela_inicial.jpg">
  <figcaption>Home screen of the web application.</figcaption>
</p>

<p align="center">
<img src="https://github.com/tarralo/ansi51_blockchain/blob/3174b8ac57e2566247ee4558f9dade6b7bb66714/models_and_results/app_bloco_minerado.jpg">
  <figcaption>Mined block screen with coordinate curve for the selected pair.</figcaption>
</p>

<p align="center">
<img src="https://github.com/tarralo/ansi51_blockchain/blob/3174b8ac57e2566247ee4558f9dade6b7bb66714/models_and_results/overview_example_ieee13bus.jpg">
  <figcaption>Results for the overcurrent relay optimization of IEEE 13 bus without DERs in CSV.</figcaption>
</p>

<p align="center">
<img src="https://github.com/tarralo/ansi51_blockchain/blob/3174b8ac57e2566247ee4558f9dade6b7bb66714/models_and_results/fitness_history_34b_sem_red.jpg">
  <figcaption>Fitness curve of the four metaheuristics for IEEE 34 bus without DERs.</figcaption>
</p>

<p align="center">
<img src="https://github.com/tarralo/ansi51_blockchain/blob/3174b8ac57e2566247ee4558f9dade6b7bb66714/models_and_results/time_history.jpg">
  <figcaption>Time evolution of the four metaheuristics for IEEE 34 bus with DERs.</figcaption>
</p>
