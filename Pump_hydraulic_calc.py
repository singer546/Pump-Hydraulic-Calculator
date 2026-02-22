import streamlit as st
import numpy as np
import math
import matplotlib.pyplot as plt

st.set_page_config(page_title="Industrial Pump Selection Tool", layout="wide")
st.title("Industrial Pump Hydraulic & Selection Tool")

g = 9.81

# ----------------------------
# UNIT CONVERSIONS
# ----------------------------

def gpm_to_m3s(gpm):
    return gpm * 0.00006309

def m3hr_to_m3s(m3hr):
    return m3hr / 3600

def ft_to_m(ft):
    return ft * 0.3048

def psi_to_Pa(psi):
    return psi * 6894.76

# ----------------------------
# FLUID PROPERTIES
# ----------------------------

def get_fluid_properties(temp_C):
    density = 1000 - 0.3 * (temp_C - 20)
    viscosity = 0.001 * np.exp(-0.02 * (temp_C - 20))
    vapor_pressure = 2330 * np.exp(0.06 * (temp_C - 20))
    return density, viscosity, vapor_pressure

# ----------------------------
# SIDEBAR INPUTS
# ----------------------------

st.sidebar.header("Process Conditions")

flow_gpm = st.sidebar.number_input("Design Flow (GPM)", value=200.0)
diam_in = st.sidebar.number_input("Pipe Diameter (inch)", value=6.0)
length_ft = st.sidebar.number_input("Pipe Length (ft)", value=300.0)
elevation_ft = st.sidebar.number_input("Static Elevation (ft)", value=20.0)
minor_k = st.sidebar.number_input("Total Minor Loss K", value=3.0)

temp_C = st.sidebar.number_input("Temperature (°C)", value=25.0)
efficiency = st.sidebar.slider("Pump Efficiency", 0.1, 1.0, 0.8)

suction_psig = st.sidebar.number_input("Suction Pressure (psig)", value=0.0)
suction_static_ft = st.sidebar.number_input("Suction Static Head (ft)", value=5.0)

# Pump Curve
st.sidebar.header("Pump Curve Data")
curve_Q_gpm = st.sidebar.text_input("Flow Points (GPM)", "100,150,200,250,300")
curve_H_ft = st.sidebar.text_input("Head Points (ft)", "120,115,105,90,70")

# NPSHr Curve
curve_NPSHr = st.sidebar.text_input("NPSHr Points (ft)", "8,10,12,16,22")

# ----------------------------
# CONVERSIONS TO SI
# ----------------------------

Q_design = gpm_to_m3s(flow_gpm)
diameter = diam_in * 0.0254
length = ft_to_m(length_ft)
elevation = ft_to_m(elevation_ft)
suction_pressure = psi_to_Pa(suction_psig)
suction_static = ft_to_m(suction_static_ft)

density, viscosity, vapor_pressure = get_fluid_properties(temp_C)

# ----------------------------
# SYSTEM CURVE GENERATION
# ----------------------------

Q_range_gpm = np.linspace(0.1, max([float(x) for x in curve_Q_gpm.split(",")])*1.2, 100)
Q_range_m3s = gpm_to_m3s(Q_range_gpm)

area = math.pi * diameter**2 / 4

system_head = []

for Q in Q_range_m3s:
    velocity = Q / area
    Re = density * velocity * diameter / viscosity
    f = 0.25 / (math.log10((0.000045 / (3.7 * diameter)) + (5.74 / (Re**0.9)))**2)
    major = f * (length/diameter) * velocity**2/(2*g)
    minor = minor_k * velocity**2/(2*g)
    TDH = major + minor + elevation
    system_head.append(TDH * 3.281)  # convert to ft

system_head = np.array(system_head)

# ----------------------------
# PUMP CURVE PROCESSING
# ----------------------------

pump_Q = np.array([float(x) for x in curve_Q_gpm.split(",")])
pump_H = np.array([float(x) for x in curve_H_ft.split(",")])
pump_NPSHr = np.array([float(x) for x in curve_NPSHr.split(",")])

# ----------------------------
# INTERSECTION (Operating Point)
# ----------------------------

interp_pump_head = np.interp(Q_range_gpm, pump_Q, pump_H)
difference = interp_pump_head - system_head

idx = np.argmin(np.abs(difference))
operating_flow = Q_range_gpm[idx]
operating_head = interp_pump_head[idx]
operating_NPSHr = np.interp(operating_flow, pump_Q, pump_NPSHr)

# ----------------------------
# NPSHa
# ----------------------------

NPSHa = ((suction_pressure/(density*g)) + suction_static 
         - (vapor_pressure/(density*g))) * 3.281

cavitation_margin = NPSHa - operating_NPSHr

# ----------------------------
# BEP Detection (Max Efficiency Assumption)
# ----------------------------

BEP_index = np.argmax(pump_H)  # simplistic assumption
BEP_flow = pump_Q[BEP_index]

# ----------------------------
# DISPLAY RESULTS
# ----------------------------

st.subheader("Operating Point")
st.write(f"Operating Flow: {operating_flow:.1f} GPM")
st.write(f"Operating Head: {operating_head:.1f} ft")
st.write(f"NPSHa: {NPSHa:.1f} ft")
st.write(f"NPSHr: {operating_NPSHr:.1f} ft")
st.write(f"Cavitation Margin: {cavitation_margin:.1f} ft")

if cavitation_margin < 3:
    st.error("⚠ Cavitation Risk – Margin < 3 ft")
else:
    st.success("Cavitation Margin Acceptable")

# ----------------------------
# PLOT
# ----------------------------

fig, ax1 = plt.subplots()

ax1.plot(pump_Q, pump_H, label="Pump Curve")
ax1.plot(Q_range_gpm, system_head, linestyle="--", label="System Curve")
ax1.scatter(operating_flow, operating_head)
ax1.axvline(BEP_flow, linestyle=":", label="BEP")

ax1.set_xlabel("Flow (GPM)")
ax1.set_ylabel("Head (ft)")
ax1.legend(loc="upper right")

# NPSH Overlay
ax2 = ax1.twinx()
ax2.plot(pump_Q, pump_NPSHr, linestyle=":", label="NPSHr")
ax2.axhline(NPSHa, linestyle="--")
ax2.set_ylabel("NPSH (ft)")

st.pyplot(fig)
