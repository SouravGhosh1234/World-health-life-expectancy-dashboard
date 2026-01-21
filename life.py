import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# পেজ কনফিগারেশন
# ---------------------------------------------------------
st.set_page_config(page_title="Global Health Analytics", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #F0F2F6; }
    div[data-testid="stMetric"] {
        background-color: #FFFFFF; border: 1px solid #E0E0E0;
        padding: 10px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    .stPlotlyChart {
        background-color: #FFFFFF; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# ডেটা লোডিং
# ---------------------------------------------------------
@st.cache_data
def load_data():
    countries = pd.read_csv("countries of the world.csv")
    life = pd.read_csv("Life Expectancy Data.csv")
    
    # Cleaning
    countries.columns = countries.columns.str.strip().str.lower()
    life.columns = life.columns.str.strip().str.lower()
    countries["country"] = countries["country"].str.strip().str.lower()
    life["country"] = life["country"].str.strip().str.lower()
    
    countries["gdp ($ per capita)"] = pd.to_numeric(countries["gdp ($ per capita)"].astype(str).str.replace(",", ""), errors="coerce")
    
    density_col = [c for c in countries.columns if "density" in c][0]
    countries.rename(columns={density_col: "population_density"}, inplace=True)
    countries["population_density"] = pd.to_numeric(countries["population_density"].astype(str).str.replace(",", "").str.strip(), errors="coerce")

    life_avg = life.groupby("country", as_index=False)[["life expectancy", "infant deaths"]].mean()
    df = pd.merge(countries, life_avg, on="country", how="inner").dropna()
    return df

df = load_data()

# ---------------------------------------------------------
# সাইডবার এবং টাইটেল
# ---------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Dashboard Settings")
    selected_region = st.selectbox("Select Region (Global Filter)", df['region'].unique())
    st.info("💡 **Brushing & Linking Enabled:** Select points on the 'GDP vs Life Expectancy' chart to filter other charts!")

# রিজিয়ন ফিল্টার (Global)
region_df = df[df['region'] == selected_region]

st.title(f"🌍 {selected_region} Analysis & Interaction")
st.write("Use the **Box Select** or **Lasso Select** tool on the first chart to filter the others.")

# ---------------------------------------------------------
# ভিজ্যুয়ালাইজেশন ও লিঙ্কিং লজিক
# ---------------------------------------------------------

# সারি ১: স্ক্যাটার প্লট (যেখানে সিলেকশন হবে) এবং ইনফ্যান্ট মর্টালিটি
col1, col2 = st.columns(2)

with col1:
    # PLOT 1: SOURCE CHART (সিলেকশন সোর্স)
    fig1 = px.scatter(
        region_df, 
        x="gdp ($ per capita)", 
        y="life expectancy", 
        size="life expectancy", 
        color="life expectancy",
        color_continuous_scale="Viridis",
        hover_name="country",
        log_x=True, 
        title="1. GDP vs Life Expectancy (Select Here!)",
        template="plotly_white"
    )
    # এই লাইনটি সিলেকশন ইভেন্ট হ্যান্ডেল করবে
    selection = st.plotly_chart(fig1, use_container_width=True, on_select="rerun", selection_mode="points")

# --- লিঙ্কিং লজিক ---
# যদি কেউ চার্টে দেশ সিলেক্ট করে, তাহলে filtered_df আপডেট হবে, না হলে পুরো region_df থাকবে
if selection and len(selection["selection"]["point_indices"]) > 0:
    selected_indices = selection["selection"]["point_indices"]
    # রিজিয়ন ডেটা থেকে ইনডেক্স অনুযায়ী ফিল্টার করা
    linked_df = region_df.iloc[selected_indices]
    st.success(f"Linked View: Showing data for {len(linked_df)} selected countries.")
else:
    linked_df = region_df # কেউ কিছু সিলেক্ট না করলে সব দেখাবে

# এখন বাকি চার্টগুলো linked_df ব্যবহার করবে
with col2:
    fig2 = px.scatter(
        linked_df, # আপডেটেড ডেটা
        x="infant deaths", 
        y="life expectancy", 
        size="population_density",
        color="infant deaths",
        color_continuous_scale="Reds",
        hover_name="country",
        title="2. Infant Mortality (Updates based on selection)",
        template="plotly_white"
    )
    st.plotly_chart(fig2, use_container_width=True)

# সারি ২: বার চার্ট এবং হিস্টোগ্রাম
col3, col4 = st.columns(2)

with col3:
    # টপ ১০ (সিলেকশন অনুযায়ী আপডেট হবে)
    if len(linked_df) > 0:
        top_data = linked_df.nlargest(10, 'life expectancy').sort_values('life expectancy', ascending=True)
        fig3 = px.bar(
            top_data, 
            x="life expectancy", 
            y="country", 
            orientation='h',
            color="life expectancy",
            color_continuous_scale="Sunsetdark",
            title="3. Top Selected Countries",
            template="plotly_white",
            text_auto='.1f'
        )
        fig3.update_layout(showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("No data selected.")

with col4:
    fig4 = px.histogram(
        linked_df, # আপডেটেড ডেটা
        x="life expectancy", 
        nbins=15,
        title="4. Life Expectancy Distribution (Updates based on selection)",
        color_discrete_sequence=['#636EFA'],
        template="plotly_white"
    )
    fig4.update_layout(bargap=0.1)
    st.plotly_chart(fig4, use_container_width=True)
