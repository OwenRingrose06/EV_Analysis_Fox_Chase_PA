<!-- PROJECT SHIELDS -->
<!--
*** I'm using markdown "reference style" links for readability.
*** Reference links are enclosed in brackets [ ] instead of parentheses ( ).
*** See the bottom of this document for the declaration of the reference variables
*** for contributors-url, forks-url, etc. This is an optional, concise syntax you may use.
*** https://www.markdownguide.org/basic-syntax/#reference-style-links
-->

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/OwenRingrose06/EV_Analysis_Fox_Chase_PA">
    <img src="https://raw.githubusercontent.com/OwenRingrose06/EV_Analysis_Fox_Chase_PA/refs/heads/master/Analysis_scripts/average_voltage_by_penetration.png?token=GHSAT0AAAAAAEJMAKFEZWBXJUYZCFLELXM22VN5XOA" alt="Logo" width="" height="">
  </a>

  <h3 align="center">EV Charging Impact Assessment on a Residential Distribution Feeder Using OpenDSS </h3>

  <p align="center">
    A 122 house study measuring the impact of EV adoption on residential feeders and transfomer Loading



<

<!-- ABOUT THE PROJECT -->
## About The Project
This project aims to measure the impact of a EV penetration on a residential distribution feeder. The feeder modeled is a small hypothetical 122 house feeder based in Fox Chase PA outside of Philadelphia. As the data is not public this model does not represent the real layout of the distribution grid of the area but is just a model of what the feeder could hypothetically look like. 

#### Feeder Topology
The layout of our feeder was designed in ArcGIS overalyed on two streets in Fox Chase PA. A reference feeder from NREL's synthetic grid data was used as a reference for designing the feeder. 

#### Modeling Baseline Loads
To get a baseline load for our system with no EV adoption the houses were modeled using NREL's ResStock data. The houses in our model were matched up to a ResStock model of the same type (ie single family detached) and of similar  square footage all located in Philadelphia County, PA. 

#### Modeling EV Loads
To generate randomized EV loads for each house in our study data was pulled from this paper. **Fang, W., Silva-Rodriguez, M., & Li, X. (2025).** _Data-Driven EV Charging Load Profile Estimation and Typical EV Daily Load Dataset Generation._ arXiv:2511.13861. This paper uses real EV charging data to generate load profiles for Electric Vehicles. Specifically all the EV loads in this model are Level 2 (240 V) medium wattage chargers. 

#### Generating DSS files
This script uses Python to generate DSS files for simulation from the exported GIS data. These scripts also are responsbile for assigning each house in the feeder daily load profiles for EV's and house baselines. 

#### Simulating EV adoption
This script generates a different set of EV load files for each of the following EV adoption  [0.00, 0.01, 0.05, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]. We then simulate our grid for a day measuring the load of each transformer and the voltage quality at each residential load. We can then plot these values over a given time to analyze voltage quality and transformer loading.

Note: Multi Family units are excluded from the study which accounts for ~20 houses. This was a decision made because residents would not be able to have a level 2 charger installed due to the reliance on street parking. 

#### Limitations
The model created in this project is not realistic of how a feeder in this area would look. We can only guess on a lot of the parameters of our distribution systems. Certain simplifications were made throughout this project most notably being that all transformers rated for 50 KVA. In reality there would be mixes of different transformers throughout the feeder. 
The most limiting factor in this model is the size however. This model is only ~120 houses large with only two laterals and two phases (one per street). A real feeder would encompass a much larger area than this. In the future I would like to expand this model to include a larger amount of houses and to properly model distance to substations. 


### Data and Tools
**Geographic / Feeder Topology**

-   Philadelphia Office of Property Assessment (OPA) — parcel data, building classifications, square footage
-   ArcGIS — feeder topology (trunk, laterals, transformer siting, service drop lengths, bus coordinates)

**Household Load Profiles**

-   NREL ResStock End-Use Load Profiles for the U.S. Building Stock — individual building timeseries data, matched by building type and square footage
-   NREL SMART-DS Dataset (Greensboro reference feeder) — conductor specifications and transformer sizing validation

**EV Charging Behavior**

-   Fang, W., Silva-Rodriguez, M., & Li, X. (2025). _Data-Driven EV Charging Load Profile Estimation and Typical EV Daily Load Dataset Generation._ arXiv:2511.13861
-   Associated dataset: _EV Daily Charging Load Profiles Estimations_, Figshare, DOI: 10.6084/m9.figshare.30601655

**Methodological References**

-   Dubey, A., & Santoso, S. (2015). _Electric Vehicle Charging on Residential Distribution Systems: Impacts and Mitigations._ IEEE Access
-   Raffoul & Li (2024/2025) — coincident peak-hour methodology precedent

### Tools & Software

-   **OpenDSS** (EPRI) — distribution system power flow simulation
-   **opendssdirect.py** — Python interface for OpenDSS
-   **Python** — pandas, numpy, matplotlib
-   **ArcGIS** — geographic data processing and feeder mapping


## Results



