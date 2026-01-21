import streamlit as st
import pandas as pd
import plotly.express as px

# Page Configuration
st.set_page_config(page_title="Global Health Analytics", layout="wide")

# Custom CSS styling
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

# Data Loading and Processing Function
@st.cache_data
def load_data():
    countries = pd.read_csv("countries of the world.csv")
    life = pd.read_csv("Life Expectancy Data.csv")
    
    # Data Cleaning
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

# Sidebar Configuration
with st.sidebar:
    st.header("Dashboard Settings")
    selected_region = st.selectbox("Select Region", df['region'].unique())
    st.info("Interactive Feature: Select points on the GDP chart to filter details across the dashboard.")

# Filter Data based on Region
region_df = df[df['region'] == selected_region]

# Main Title
st.title(f"Global Health Analytics: {selected_region}")
st.write("Analyze the relationship between GDP, Life Expectancy, and Mortality. Use the selection tool on the first chart for deep-dive analysis.")

# Layout: Row 1
col1, col2 = st.columns(2)

with col1:
    fig1 = px.scatter(
        region_df, 
        x="gdp ($ per capita)", 
        y="life expectancy", 
        size="life expectancy", 
        color="life expectancy",
        color_continuous_scale="Viridis",
        hover_name="country",
        log_x=True, 
        title="GDP vs Life Expectancy (Interactive Selection)",
        template="plotly_white"
    )
    # Selection Logic
    selection = st.plotly_chart(fig1, use_container_width=True, on_select="rerun", selection_mode="points")

# Brushing & Linking Logic
if selection and len(selection["selection"]["point_indices"]) > 0:
    selected_indices = selection["selection"]["point_indices"]
    linked_df = region_df.iloc[selected_indices]
    st.success(f"Displaying analysis for {len(linked_df)} selected countries.")
else:
    linked_df = region_df

with col2:
    fig2 = px.scatter(
        linked_df, 
        x="infant deaths", 
        y="life expectancy", 
        size="population_density",
        color="infant deaths",
        color_continuous_scale="Reds",
        hover_name="country",
        title="Infant Mortality Analysis",
        template="plotly_white"
    )
    st.plotly_chart(fig2, use_container_width=True)

# Layout: Row 2
col3, col4 = st.columns(2)

with col3:
    if len(linked_df) > 0:
        top_data = linked_df.nlargest(10, 'life expectancy').sort_values('life expectancy', ascending=True)
        fig3 = px.bar(
            top_data, 
            x="life expectancy", 
            y="country", 
            orientation='h',
            color="life expectancy",
            color_continuous_scale="Sunsetdark",
            title="Top Countries by Life Expectancy",
            template="plotly_white",
            text_auto='.1f'
        )
        fig3.update_layout(showlegend=False)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("No countries selected.")

with col4:
    fig4 = px.histogram(
        linked_df, 
        x="life expectancy", 
        nbins=15,
        title="Life Expectancy Distribution",
        color_discrete_sequence=['#636EFA'],
        template="plotly_white"
    )
    fig4.update_layout(bargap=0.1)
    st.plotly_chart(fig4, use_container_width=True)
