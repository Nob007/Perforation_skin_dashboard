import streamlit as st
import pandas as pd
import numpy as np

st.title("Flow Efficiency")
col1, col2, col3 = st.columns(3)
re= col1.number_input("Drainage radius (ft)", min_value = 0.0, value = 630.0)
rw=col2.number_input("Well Radius (in)", min_value = 0.0, value = 4.25)
s=col3.number_input("Skin", value = 1.5)

Flow_efficiency = np.log(re*12.0/rw)/(np.log(re*12/rw) + s)

st.metric("Flow Efficiency", value = f"{Flow_efficiency}")
