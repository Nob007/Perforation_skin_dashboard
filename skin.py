import numpy as np
import streamlit as st
import scipy
import pandas as pd
import plotly.graph_objects as go

st.title("Skin Calculation and Analysis")

angles = [0, 45, 60, 90, 120, 180]
alpha = [0, 0.86, 0.813, 0.726, 0.648, 0.5]
C1 = [0.16, 0.000046, 0.0003, 0.0019, 0.0066, 0.026]
C2 = [2.675, 8.791, 7.509, 6.155, 5.32, 4.532]
a1 = [-2.091, -1.788, -1.898, -1.905, -2.018, -2.025]
a2 = [0.0453, 0.2398, 0.1023, 0.1038, 0.0634, 0.0943]
b1 = [5.1313, 1.1915, 1.3654, 1.5674, 1.6136, 3.0373]
b2 = [1.8672,1.6392, 1.649, 1.6935, 1.777, 1.8115]

col1, col2, col3, col4 = st.columns(4)
rw = col1.number_input("Well radius(in)", min_value = 0.0, value = 4.25)
lp = col2.number_input("Perforation length(in)", min_value = 0.0, value = 12.0)
h = col3.number_input("Spacing(in)", min_value = 0.0, value = 2.0)
# spf = col3.metric("Shot density(12/spacing)", value = f"{12/h}")
rp = col4.number_input("Perforation radius(in)", min_value = 0.0, value = 0.16)
phasing_angle = col4.selectbox(
    "Phasing Angle (degrees)",
    [0, 45, 60, 90, 120, 180]
)
perm_ratio = col1.selectbox("Permeability ratios", ["kv/kh", "kc/k", "kd/k"])
kv_kh = 1
kc_k = 0.2
kd_k = 0.5
match(perm_ratio):
    case "kv/kh":
        kv_kh = col2.number_input("kv/kh", min_value = 0.0, value = 1.0)
    case "kc/k":
        kc_k = col2.number_input("kc/k", min_value = 0.0, value = 0.2)
    case "kd/k":
        kd_k = col2.number_input("kd/k", min_value = 0.0, value = 0.5)
ld = col3.number_input("Damaged length(in)", min_value = 0.0, value = 3.0)
rc = col1.number_input("Crushed zone radius(in)", min_value = 0.0, value = 0.5)


lp_ = lp - (1.0- kd_k)*ld if lp<ld else  lp
rw_ = rw - (1.0-kd_k)*ld if lp<ld else rw
spf = 12.0/h
col1, col2, col3 = st.columns(3)
col1.metric("Effective Perforation Length(in)", value = f"{lp_}")
col2.metric("Effective Well Radius(in)", value = f"{rw_}")
col3.metric("Shot Density", value = f"{spf}")

def calculate_skin(rw, lp, h, rp, phasing_angle, kv_kh, kc_k, kd_k, ld, rc):
    phasing = angles.index(phasing_angle)
    lp_ = lp - (1.0 - kd_k) * ld if lp < ld else lp
    rw_ = rw - (1.0 - kd_k) * ld if lp < ld else rw
    rwD = rw_/(rw_+lp_)
    hD = (h/lp_)*np.sqrt(1/kv_kh)
    rpD = (rp/(2*h))*(1+np.sqrt(kv_kh))
    a = a1[phasing]*np.log10(rpD) + a2[phasing]
    b = b1[phasing]*rpD + b2[phasing]
    Sh = np.log(rw_/(alpha[phasing]*(rw_+lp_))) if phasing_angle != 0 else np.log(4*rw_/lp_)
    Swb = C1[phasing]*np.exp(C2[phasing]*rwD)
    Sv = (10**a)*(hD**(b-1))*(rpD**b)
    Sc = (h/lp_)*(1/kc_k - 1)*np.log(rc/rp)
    Sp = Sh + Swb + Sv + Sc
    return Sh, Swb, Sv, Sc, Sp

Sh, Swb, Sv, Sc, Sp = calculate_skin(rw, lp, h, rp, phasing_angle, kv_kh, kc_k, kd_k, ld, rc)
col1, col2, col3, col4 = st.columns(4)
col1.metric("Horizontal Skin", value = f"{Sh:,.4f}")
col2.metric("Wellbore Skin", value = f"{Swb:,.4f}")
col3.metric("Vertical Skin", value = f"{Sv:,.4f}")
col4.metric("Crushed zone Skin", value = f"{Sc:,.4f}")
st.metric("**Perforation skin**", value = f"{Sp:,.4f}")



col1, col2 = st.columns(2)
df1 = col1.data_editor(
    pd.DataFrame({"Shot Density":[2,4,6,8]}),
    num_rows="dynamic"
)
df2 = col2.data_editor(
    pd.DataFrame({"Perforation Length":[2,4,6,8]}),
    num_rows="dynamic"
)
shot_densities = df1["Shot Density"].values
lp_values = df2["Perforation Length"].values

st.subheader("Perforation Skin vs Perforation Length")
 
fig = go.Figure()
angles_req = [0,90, 180]
for angle in angles_req:
    for spf in shot_densities:
        h_val = 12/spf
        Sp_vals = []
        for lp_i in lp_values:

            _,_,_,_,Sp_i = calculate_skin(
                rw, lp_i, h_val, rp,
                angle, kv_kh, kc_k, kd_k, ld, rc
            )

            Sp_vals.append(Sp_i)

        fig.add_trace(
            go.Scatter(
                x=lp_values,
                y=Sp_vals,
                mode="lines",
                name=f"{angle}°, SPF={spf}"
            )
        )

fig.update_layout(
    xaxis_title="Perforation Length (in)",
    yaxis_title="Perforation Skin",
)

st.plotly_chart(fig, use_container_width=True)



st.subheader("Skin vs Lp")
fig_small = go.Figure()
Sh_vals1 = []
Swb_vals1 = []
Sv_vals1 = []
Sc_vals1 = []
Sp_vals1 = []
for lp_i in lp_values:
    Sh_i,Swb_i,Sv_i,Sc_i,Sp_i = calculate_skin(
        rw, lp_i, h, rp,
        angle, kv_kh, kc_k, kd_k, ld, rc
            )
    Sh_vals1.append(Sh_i)
    Swb_vals1.append(Swb_i)
    Sv_vals1.append(Sv_i)
    Sc_vals1.append(Sc_i)
    Sp_vals1.append(Sp_i)
fig_small.add_trace(
    go.Scatter(x=lp_values, y=Sh_vals1, mode="lines", name="Horizontal Skin")
)
fig_small.add_trace(
    go.Scatter(x=lp_values, y=Swb_vals1, mode="lines", name="Wellbore Skin")
)

fig_small.add_trace(
    go.Scatter(x=lp_values, y=Sv_vals1, mode="lines", name="Vertical Skin")
)

fig_small.add_trace(
    go.Scatter(x=lp_values, y=Sc_vals1, mode="lines", name="Crushed Zone Skin")
)

fig_small.add_trace(
    go.Scatter(x=lp_values, y=Sp_vals, mode="lines", name="Total Skin")
)

fig_small.update_layout(
    xaxis_title="Perforation Length (in)",
    yaxis_title="Perforation Skin",
)

st.plotly_chart(fig_small, use_container_width=True)


st.subheader("Skin vs spf")
fig_small2 = go.Figure()
Sh_vals2 = []
Swb_vals2 = []
Sv_vals2 = []
Sc_vals2 = []
Sp_vals2 = []
for spf in shot_densities:
    h_val = 12/spf
    Sh_i,Swb_i,Sv_i,Sc_i,Sp_i = calculate_skin(
        rw, lp, h_val, rp,
        angle, kv_kh, kc_k, kd_k, ld, rc
            )
    Sh_vals2.append(Sh_i)
    Swb_vals2.append(Swb_i)
    Sv_vals2.append(Sv_i)
    Sc_vals2.append(Sc_i)
    Sp_vals2.append(Sp_i)
fig_small2.add_trace(
    go.Scatter(x=shot_densities, y=Sh_vals2, mode="lines", name="Horizontal Skin")
)
fig_small2.add_trace(
    go.Scatter(x=shot_densities, y=Swb_vals2, mode="lines", name="Wellbore Skin")
)

fig_small2.add_trace(
    go.Scatter(x=shot_densities, y=Sv_vals2, mode="lines", name="Vertical Skin")
)

fig_small2.add_trace(
    go.Scatter(x=shot_densities, y=Sc_vals2, mode="lines", name="Crushed Zone Skin")
)

fig_small2.add_trace(
    go.Scatter(x=shot_densities, y=Sp_vals2, mode="lines", name="Total Skin")
)

fig_small2.update_layout(
    xaxis_title="Shot Density",
    yaxis_title="Perforation Skin",
)

st.plotly_chart(fig_small2, use_container_width=True)


st.subheader("Skin vs phasing angles")
fig_small3 = go.Figure()
Sh_vals3 = []
Swb_vals3 = []
Sv_vals3= []
Sc_vals3 = []
Sp_vals3 = []
for angle in angles:
    Sh_i,Swb_i,Sv_i,Sc_i,Sp_i = calculate_skin(
        rw, lp, h, rp,
        angle, kv_kh, kc_k, kd_k, ld, rc
            )
    Sh_vals3.append(Sh_i)
    Swb_vals3.append(Swb_i)
    Sv_vals3.append(Sv_i)
    Sc_vals3.append(Sc_i)
    Sp_vals3.append(Sp_i)
fig_small3.add_trace(
    go.Scatter(x=angles, y=Sh_vals3, mode="lines", name="Horizontal Skin")
)
fig_small3.add_trace(
    go.Scatter(x=angles, y=Swb_vals3, mode="lines", name="Wellbore Skin")
)

fig_small3.add_trace(
    go.Scatter(x=angles, y=Sv_vals3, mode="lines", name="Vertical Skin")
)

fig_small3.add_trace(
    go.Scatter(x=angles, y=Sc_vals3, mode="lines", name="Crushed Zone Skin")
)

fig_small3.add_trace(
    go.Scatter(x=angles, y=Sp_vals3, mode="lines", name="Total Skin")
)

fig_small3.update_layout(
    xaxis_title="Phasing Angles",
    yaxis_title="Perforation Skin",
)

st.plotly_chart(fig_small3, use_container_width=True)




