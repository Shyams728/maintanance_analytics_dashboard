"""
Styles Module
Centralized styling configuration for the analytics dashboard.
"""

import streamlit as st

# =============================================================================
# COLOR PALETTE
# =============================================================================

COLORS = {
    # Primary brand colors
    'primary': '#1f77b4',
    'primary_dark': '#0d5293',
    'primary_light': '#5aa8e0',
    
    # Status colors
    'success': '#2ecc71',
    'warning': '#f39c12',
    'danger': '#e74c3c',
    'info': '#3498db',
    
    # Neutral colors
    'dark': '#2c3e50',
    'gray': '#7f8c8d',
    'light': '#ecf0f1',
    'white': '#ffffff',
    
    # Chart colors
    'chart_palette': [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', 
        '#9467bd', '#8c564b', '#e377c2', '#7f7f7f'
    ],
    
    # Gradient colors
    'gradient_start': '#667eea',
    'gradient_end': '#764ba2'
}

# =============================================================================
# PLOTLY TEMPLATE
# =============================================================================

PLOTLY_TEMPLATE = {
    'layout': {
        'font': {'family': 'Inter, sans-serif', 'color': COLORS['dark']},
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(0,0,0,0)',
        'colorway': COLORS['chart_palette'],
        'title': {'font': {'size': 16, 'color': COLORS['dark']}},
        'legend': {'orientation': 'h', 'yanchor': 'bottom', 'y': -0.2}
    }
}

# =============================================================================
# CSS INJECTION
# =============================================================================

CUSTOM_CSS = """
<style>
    /* Import Google Font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    /* Global font */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Metric cards styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
        color: #1f77b4;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem;
        font-weight: 500;
        color: #2c3e50;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.85rem;
    }
    
    /* Header styling */
    h1 {
        color: #2c3e50;
        font-weight: 700;
        border-bottom: 3px solid #1f77b4;
        padding-bottom: 10px;
    }
    
    h2, h3 {
        color: #34495e;
        font-weight: 600;
    }
    
    /* Subheader styling */
    .stSubheader {
        color: #2c3e50;
        font-weight: 600;
    }
    
    /* Card-like containers */
    [data-testid="stVerticalBlock"] > [data-testid="stHorizontalBlock"] {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
        border-right: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Force all text in sidebar to be white */
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    
    /* Fix for Selectbox/Multiselect backgrounds */
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: rgba(0, 0, 0, 0.3) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
        color: white !important;
    }
    
    /* Fix for dropdown options text color (when opened) - hacky but needed */
    ul[data-testid="stSelectboxVirtualDropdown"] li {
        color: #2c3e50 !important; /* revert to dark for white dropdowns */
    }
    
    /* Fix for MultiSelect tags */
    [data-testid="stSidebar"] [data-baseweb="tag"] {
        background-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Standard Inputs */
    [data-testid="stSidebar"] input {
        color: white !important;
    }
    
    /* Success/Warning/Error containers */
    .success-box {
        background-color: rgba(46, 204, 113, 0.1);
        border-left: 4px solid #2ecc71;
        padding: 1rem;
        border-radius: 4px;
    }
    
    .warning-box {
        background-color: rgba(243, 156, 18, 0.1);
        border-left: 4px solid #f39c12;
        padding: 1rem;
        border-radius: 4px;
    }
    
    .danger-box {
        background-color: rgba(231, 76, 60, 0.1);
        border-left: 4px solid #e74c3c;
        padding: 1rem;
        border-radius: 4px;
    }
    
    /* Table styling */
    .dataframe {
        font-size: 0.85rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        transition: transform 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
</style>
"""


def inject_custom_css():
    """Inject custom CSS into the Streamlit app."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_currency(value: float, prefix: str = "₹") -> str:
    """Format number as currency with Indian locale."""
    if value >= 10000000:  # 1 Crore
        return f"{prefix}{value/10000000:.2f} Cr"
    elif value >= 100000:  # 1 Lakh
        return f"{prefix}{value/100000:.2f} L"
    elif value >= 1000:
        return f"{prefix}{value/1000:.1f}K"
    else:
        return f"{prefix}{value:,.0f}"


def format_number(value: float) -> str:
    """Format large numbers with K/M suffix."""
    if value >= 1000000:
        return f"{value/1000000:.2f}M"
    elif value >= 1000:
        return f"{value/1000:.1f}K"
    else:
        return f"{value:,.0f}"


def get_status_color(status: str) -> str:
    """Get color based on status string."""
    status_lower = status.lower()
    if 'critical' in status_lower or 'danger' in status_lower or 'over' in status_lower:
        return COLORS['danger']
    elif 'warning' in status_lower or 'risk' in status_lower:
        return COLORS['warning']
    elif 'healthy' in status_lower or 'good' in status_lower or 'on track' in status_lower:
        return COLORS['success']
    else:
        return COLORS['gray']


def status_badge(status: str) -> str:
    """Create an HTML status badge."""
    color = get_status_color(status)
    return f"""
    <span style="
        background-color: {color}; 
        color: white; 
        padding: 4px 12px; 
        border-radius: 12px; 
        font-size: 0.8rem;
        font-weight: 600;
    ">{status}</span>
    """


def metric_card(label: str, value: str, delta: str = None, delta_color: str = "normal") -> None:
    """Display a styled metric card."""
    st.metric(label=label, value=value, delta=delta, delta_color=delta_color)


def section_header(title: str, icon: str = None) -> None:
    """Display a section header with optional icon."""
    if icon:
        st.markdown(f"### {icon} {title}")
    else:
        st.markdown(f"### {title}")


# =============================================================================
# CHART STYLING HELPERS
# =============================================================================

def style_plotly_chart(fig, height: int = 400):
    """Apply consistent styling to a Plotly figure."""
    fig.update_layout(
        height=height,
        font=dict(family='Inter, sans-serif'),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=60, b=40),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=-0.2,
            xanchor='center',
            x=0.5
        )
    )
    
    # Style axes
    fig.update_xaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)',
        showline=True,
        linewidth=1,
        linecolor='rgba(128,128,128,0.3)'
    )
    fig.update_yaxes(
        showgrid=True,
        gridwidth=1,
        gridcolor='rgba(128,128,128,0.1)',
        showline=True,
        linewidth=1,
        linecolor='rgba(128,128,128,0.3)'
    )
    
    return fig


# =============================================================================
# GAUGE CHART HELPERS
# =============================================================================

def get_gauge_color(value: float, thresholds: tuple = (70, 90)) -> str:
    """Get color for gauge based on value and thresholds."""
    if value < thresholds[0]:
        return COLORS['danger']
    elif value < thresholds[1]:
        return COLORS['warning']
    else:
        return COLORS['success']

def get_kpi_hints():
    """Returns a dictionary of KPI hints."""
    return {
        "OEE_Pct": "Overall Equipment Effectiveness: A measure of how well a manufacturing operation is utilized.",
        "Availability_Pct": "The percentage of scheduled time that the equipment is available to operate.",
        "MTTR_Hours": "Mean Time To Repair: The average time required to repair a failed component or device.",
        "MTBF_Hours": "Mean Time Between Failures: The predicted elapsed time between inherent failures of a mechanical or electronic system.",
        "Planned_Maintenance_Pct": "The percentage of maintenance work that is planned, rather than reactive."
    }

def kpi_card(title, value, hint, sub_value=None):
    """Generates a KPI card with a title, value, and hint."""

    sub_value_html = f'<p style="font-size: 0.9rem; color: #bbb;">{sub_value}</p>' if sub_value else ""

    st.markdown(f"""
    <div style="background-color: #222; border-radius: 10px; padding: 20px; text-align: center;">
        <h3 style="color: #fff;">{title}</h3>
        <p style="font-size: 2rem; font-weight: bold; color: #00bfff;">{value}</p>
        {sub_value_html}
        <p style="font-size: 0.9rem; color: #bbb;">{hint}</p>
    </div>
    """, unsafe_allow_html=True)
