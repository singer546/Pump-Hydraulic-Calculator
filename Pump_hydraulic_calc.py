import streamlit as st
import numpy as np
import math
import matplotlib.pyplot as plt

st.set_page_config(page_title="Pump Hydraulic Calculator", layout="wide")
st.title("Pump Hydraulic Calculation Tool")

g = 9.81

# ----------------------------
# UNIT CONVERSIONS
# ----------------------------

def flow_to_m3s(value, unit):
    if unit == "m3/hr":
        return value / 3600
    elif unit == "m3/s":
        return value
    elif unit == "GPM":
        return value * 0.00006309
    return value

def length_to_m(value, unit):
    if unit == "m":
        return value
    elif unit == "ft":
        return value * 0.3048
    elif unit == "inch":
        return value * 0.0254
    return value

def pressure_to_Pa(value, unit):
    if unit == "Pa":
        return value
    elif unit == "kPa":
        return value * 1000
    elif unit == "bar":
        return value * 100000
    elif unit == "psig":
        return value * 6894.76
    return value

def temperature_to_C(value, unit):
    if unit == "°C":
        return value
    elif unit == "°F":
        return (value - 32) * 5/9
    return value

def power_from_W(value, unit):
    if unit == "kW":
        return value / 1000
    elif unit == "HP":
        return value / 745.7
    return value

# ----------------------------
# FLUID PROPERTIES
# ----------------------------

def get_fluid_properties(fluid, temperature_C):
    if fluid == "Water":
        density = 1000 - 0.3 * (temperature_C - 20)
        viscosity = 0.001 * np.exp(-0.02 * (temperature_C - 20))
    elif fluid == "Light Oil":
        density = 850
        viscosity = 0.02
    elif fluid == "Seawater":
        density = 1025
        viscosity = 0.0012
    else:
        density = 1000
        viscosity = 0.001

    vapor_pressure = 2330 * np.exp(0.06 * (temperature_C - 20))
    return density, viscosity, vapor_pressure

# ----------------------------
# SIDEBAR INPUTS
# ----------------------------

st.sidebar.header("Process Inputs")

fluid = st.sidebar.selectbox("Fluid", ["Water", "Light Oil", "Seawater"])

temp_unit = st.sidebar.selectbox("Temperature Unit", ["°C", "°F"])
temperature_input = st.sidebar.number_input("Temperature", value=25.0)
temperature = temperature_to_C(temperature_input, temp_unit)

flow_unit = st.sidebar.selectbox("Flow Unit", ["m3/hr", "m3/s", "GPM"])
flow_input = st.sidebar.number_input("Flow Rate", value=50.0)
Q = flow_to_m3s(flow_input, flow_unit)

diam_unit = st.sidebar.selectbox("Diameter Unit", ["m", "inch"])
diam_input = st.sidebar.number_input("Pipe Diameter", value=0.1)
diameter = length_to_m(diam_input, diam_unit)

len_unit = st.sidebar.selectbox("Length/Head Unit", ["m", "ft"])
length_input = st.sidebar.number_input("Pipe Length", value=200.0)
length = length_to_m(length_input, len_unit)

elev_input = st.sidebar.number_input("Elevation Head", value=10.0)
elevation = length_to_m(elev_input, len_unit)

roughness = st.sidebar.number_input("Pipe Roughness (m)", value=0.000045)
minor_k = st.sidebar.number_input("Total Minor Loss K", value=2.0)

efficiency = st.sidebar.slider("Pump Efficiency", 0.1, 1.0, 0.75)

pressure_unit = st.sidebar.selectbox("Pressure Unit", ["Pa", "kPa", "bar", "psig"])
suction_pressure_input = st.sidebar.number_input("Suction Pressure", value=101325.0)
suction_pressure = pressure_to_Pa(suction_pressure_input, pressure_unit)

suction_static_input = st.sidebar.number_input("Suction Static Head", value=2.0)
suction_static = length_to_m(suction_static_input, len_unit)

power_unit = st.sidebar.selectbox("Power Output Unit", ["kW", "HP"])

# Pump Curve
st.sidebar.header("Pump Curve")
curve_Q = st.sidebar.text_input("Flow Points (comma separated)", "10,30,50,70")
curve_H = st.sidebar.text_input("Head Points (comma separated)", "40,35,30,20")

# ----------------------------
# CALCULATIONS
# ----------------------------

density, viscosity, vapor_pressure = get_fluid_properties(fluid, temperature)

area = math.pi * diameter**2 / 4
velocity = Q / area
Re = density * velocity * diameter / viscosity

if Re > 4000:
    f = 0.25 / (math.log10((roughness / (3.7 * diameter)) + (5.74 / (Re**0.9)))**2)
else:
    f = 64 / Re

major_loss = f * (length/diameter) * velocity**2/(2*g)
minor_loss = minor_k * velocity**2/(2*g)
TDH = major_loss + minor_loss + elevation

hydraulic_power_W = density * g * Q * TDH
shaft_power_W = hydraulic_power_W / efficiency

NPSHa = (suction_pressure/(density*g)) + suction_static \
        - (vapor_pressure/(density*g)) \
        - major_loss

# ----------------------------
# DISPLAY
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
    st.write(f"Hydraulic Power: {power_from_W(hydraulic_power_W, power_unit):.2f} {power_unit}")
    st.write(f"Shaft Power: {power_from_W(shaft_power_W, power_unit):.2f} {power_unit}")
    st.write(f"NPSH Available: {NPSHa:.2f} m")

# ----------------------------
# PUMP CURVE
# ----------------------------

try:
    Q_curve = np.array([float(x) for x in curve_Q.split(",")])
    H_curve = np.array([float(x) for x in curve_H.split(",")])

    fig, ax = plt.subplots()
    ax.plot(Q_curve, H_curve)
    ax.scatter(flow_input, TDH)
    ax.set_xlabel(f"Flow ({flow_unit})")
    ax.set_ylabel("Head (m)")
    ax.set_title("Pump Curve")
    st.pyplot(fig)
except:
    st.warning("Check pump curve input format.")
