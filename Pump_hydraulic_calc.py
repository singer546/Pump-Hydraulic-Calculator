import streamlit as st
import numpy as np
import math
import matplotlib.pyplot as plt

st.set_page_config(page_title="Pump Hydraulic Calculator", layout="wide")

st.title("Pump Hydraulic Calculation Tool")

# ----------------------------
# FLUID PROPERTY DATABASE
# ----------------------------

def get_fluid_properties(fluid, temperature):
    # Approximate properties
    if fluid == "Water":
        density = 1000 - 0.3 * (temperature - 20)
        viscosity = 0.001 * np.exp(-0.02 * (temperature - 20))
    elif fluid == "Light Oil":
        density = 850
        viscosity = 0.02
    elif fluid == "Seawater":
        density = 1025
        viscosity = 0.0012
    else:
        density = 1000
        viscosity = 0.001

    vapor_pressure = 2330 * np.exp(0.06 * (temperature - 20))  # rough Pa
    return density, viscosity, vapor_pressure


# ----------------------------
# USER INPUTS
# ----------------------------

st.sidebar.header("Process Inputs")

fluid = st.sidebar.selectbox("Fluid", ["Water", "Light Oil", "Seawater"])
temperature = st.sidebar.slider("Temperature (°C)", 0, 100, 25)

flow_rate = st.sidebar.number_input("Flow Rate (m³/hr)", 1.0, 10000.0, 50.0)
diameter = st.sidebar.number_input("Pipe Diameter (m)", 0.01, 2.0, 0.1)
length = st.sidebar.number_input("Pipe Length (m)", 1.0, 5000.0, 200.0)
roughness = st.sidebar.number_input("Pipe Roughness (m)", 0.000001, 0.01, 0.000045)
elevation = st.sidebar.number_input("Elevation Head (m)", -100.0, 500.0, 10.0)

minor_k = st.sidebar.number_input("Total Minor Loss K-value", 0.0, 100.0, 2.0)

efficiency = st.sidebar.slider("Pump Efficiency", 0.1, 1.0, 0.75)

# NPSH Inputs
suction_pressure = st.sidebar.number_input("Suction Surface Pressure (Pa)", 0.0, 500000.0, 101325.0)
suction_static_head = st.sidebar.number_input("Suction Static Head (m)", -20.0, 50.0, 2.0)

# Pump Curve Inputs
st.sidebar.header("Pump Curve (Head vs Flow)")
curve_Q = st.sidebar.text_input("Flow Points (m³/hr, comma separated)", "10,30,50,70")
curve_H = st.sidebar.text_input("Head Points (m, comma separated)", "40,35,30,20")

# ----------------------------
# CALCULATIONS
# ----------------------------

density, viscosity, vapor_pressure = get_fluid_properties(fluid, temperature)

Q = flow_rate / 3600
area = math.pi * diameter**2 / 4
velocity = Q / area

Re = density * velocity * diameter / viscosity

if Re > 4000:
    f = 0.25 / (math.log10((roughness / (3.7 * diameter)) + (5.74 / (Re**0.9)))**2)
else:
    f = 64 / Re

g = 9.81

major_loss = f * (length/diameter) * velocity**2/(2*g)
minor_loss = minor_k * velocity**2/(2*g)

TDH = major_loss + minor_loss + elevation

hydraulic_power = density * g * Q * TDH
shaft_power = hydraulic_power / efficiency

# ----------------------------
# NPSH AVAILABLE
# ----------------------------

NPSHa = (suction_pressure/(density*g)) + suction_static_head \
        - (vapor_pressure/(density*g)) \
        - major_loss

# ----------------------------
# DISPLAY RESULTS
# ----------------------------

col1, col2 = st.columns(2)

with col1:
    st.subheader("Hydraulic Results")
    st.write(f"Velocity: {velocity:.2f} m/s")
    st.write(f"Reynolds Number: {Re:.0f}")
    st.write(f"Friction Factor: {f:.4f}")
    st.write(f"Major Loss: {major_loss:.2f} m")
    st.write(f"Minor Loss: {minor_loss:.2f} m")
    st.write(f"Total Dynamic Head: {TDH:.2f} m")

with col2:
    st.subheader("Power & NPSH")
    st.write(f"Hydraulic Power: {hydraulic_power/1000:.2f} kW")
    st.write(f"Shaft Power: {shaft_power/1000:.2f} kW")
    st.write(f"NPSH Available: {NPSHa:.2f} m")

# ----------------------------
# PUMP CURVE PLOT
# ----------------------------

try:
    Q_curve = np.array([float(x) for x in curve_Q.split(",")])
    H_curve = np.array([float(x) for x in curve_H.split(",")])

    fig, ax = plt.subplots()
    ax.plot(Q_curve, H_curve)
    ax.scatter(flow_rate, TDH)
    ax.set_xlabel("Flow (m³/hr)")
    ax.set_ylabel("Head (m)")
    ax.set_title("Pump Curve")
    st.pyplot(fig)
except:
    st.warning("Check pump curve input format.")