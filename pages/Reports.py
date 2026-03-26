"""
Reports Page - With Visual Matplotlib Charts
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime
import matplotlib.pyplot as plt
from sidebar import create_sidebar

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable, Image
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

st.set_page_config(page_title="Reports", page_icon="📄", layout="wide")

# --- CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .stApp { background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%); }
    #MainMenu, footer, header, [data-testid="stToolbar"], [data-testid="stSidebarNav"] { display: none !important; }
    .block-container { padding: 2rem 3rem !important; }
    
    h1, h2, h3 { color: #ffffff !important; }
    h1 { background: linear-gradient(135deg, #6366f1, #8b5cf6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    p, span, label { color: #a0a0a0 !important; }
    
    [data-testid="stMetric"] { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 1rem; }
    .stButton > button { background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; color: white !important; border: none !important; border-radius: 8px !important; }
    hr { border-color: rgba(255,255,255,0.1) !important; }
    .streamlit-expanderHeader { background: rgba(255,255,255,0.05) !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)


def main():
    create_sidebar()

    st.markdown("<h1>📄 Report Generator</h1>", unsafe_allow_html=True)
    st.caption("Create professional PDF reports (Models will auto-run if not trained yet)")
    
    if st.session_state.get('data') is None:
        st.warning("⚠️ No data loaded.")
        st.stop()
    
    df = st.session_state['data']
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚙️ Options")
        include_products = st.checkbox("📦 Top Products Table", True)
        n_products = st.slider("Products count", 5, 20, 10) if include_products else 10
    
    with col2:
        st.markdown("### 📊 Include Sections")
        include_charts = st.checkbox("📈 Visual Charts", value=True)
        include_basket = st.checkbox("🛒 Basket Analysis", value=True)
        include_forecast = st.checkbox("🤖 AI Forecast", value=True)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("📝 Generate Report", type="primary", use_container_width=True):
            with st.spinner("Compiling data and rendering charts..."):
                
                # --- AUTO-RUN BASKET ANALYSIS ---
                if include_basket and st.session_state.get('basket_rules') is None:
                    try:
                        from pages.Basket_Analysis import run_analysis
                        rules = run_analysis(df, min_support=0.02, min_lift=1.2)
                        st.session_state['basket_rules'] = rules
                    except Exception as e:
                        st.error(f"Basket Analysis Auto-Run Error: {e}")
                        include_basket = False

                # --- AUTO-RUN AI FORECAST ---
                if include_forecast and st.session_state.get('model_results') is None:
                    try:
                        from pages.AI_forecasting import train_models
                        daily = df.groupby('order_date')['total_value'].sum().reset_index()
                        daily = daily.set_index('order_date').resample('D').sum().reset_index().sort_values('order_date')
                        
                        if len(daily) >= 14:
                            results = train_models(daily)
                            st.session_state['model_results'] = results
                        else:
                            st.warning("Not enough data (need 14 days) for AI forecasting. Skipping section.")
                            include_forecast = False
                    except Exception as e:
                        st.error(f"AI Forecast Auto-Run Error: {e}")
                        include_forecast = False

                # Generate the actual PDF
                pdf = generate_pdf(df, include_products, include_basket, include_forecast, n_products, include_charts)
                st.session_state['pdf_buffer'] = pdf
                
            st.success("✅ Report Ready!")
    
    if st.session_state.get('pdf_buffer'):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.download_button(
                "⬇️ Download PDF", 
                st.session_state['pdf_buffer'], 
                f"SME_Sales_Report_{datetime.now().strftime('%Y%m%d')}.pdf", 
                "application/pdf", 
                use_container_width=True
            )

# --- CHART GENERATION ENGINE ---
def create_trend_chart(df):
    """Generates a daily revenue line chart and returns it as an Image flowable"""
    if not pd.api.types.is_datetime64_any_dtype(df['order_date']):
        df['order_date'] = pd.to_datetime(df['order_date'])
        
    daily = df.groupby(df['order_date'].dt.date)['total_value'].sum()
    
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.plot(daily.index, daily.values, color='#6366f1', linewidth=2, marker='o', markersize=4)
    ax.set_title('Daily Revenue Trend', fontsize=12, pad=10, color='#333333', fontweight='bold')
    ax.set_ylabel('Revenue (£)', fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Remove top and right borders for a cleaner look
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    img_buffer.seek(0)
    
    return Image(img_buffer, width=6.5*inch, height=2.8*inch)

def create_top_products_chart(df):
    """Generates a horizontal bar chart of top 5 products"""
    top5 = df.groupby('product_name')['total_value'].sum().nlargest(5).sort_values(ascending=True)
    
    fig, ax = plt.subplots(figsize=(8, 3))
    bars = ax.barh(top5.index.astype(str).str[:25] + '...', top5.values, color='#10b981')
    ax.set_title('Top 5 Products by Revenue', fontsize=12, pad=10, color='#333333', fontweight='bold')
    ax.set_xlabel('Revenue (£)', fontsize=10)
    
    # Add value labels to the end of bars
    for bar in bars:
        ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2, f' £{bar.get_width():,.0f}', 
                va='center', ha='left', fontsize=9, color='#333333')
                
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    img_buffer.seek(0)
    
    return Image(img_buffer, width=6.5*inch, height=2.5*inch)

# --- PDF GENERATION ENGINE ---
def generate_pdf(df, include_products, include_basket, include_forecast, n_products, include_charts):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
    
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=24, alignment=TA_CENTER, textColor=colors.HexColor('#6366f1'))
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, textColor=colors.HexColor('#1a1a2e'), spaceBefore=20, spaceAfter=10)
    
    # Header
    story.append(Paragraph("SME Analytics - Comprehensive Report", title_style))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", ParagraphStyle('Date', alignment=TA_CENTER, textColor=colors.grey)))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#6366f1')))
    story.append(Spacer(1, 0.2*inch))
    
    # 1. Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    data = [
        ['Metric', 'Value'], 
        ['Total Revenue', f"£{df['total_value'].sum():,.2f}"], 
        ['Total Orders', f"{len(df):,}"], 
        ['Average Order Value', f"£{df['total_value'].mean():.2f}"], 
        ['Unique Products Sold', f"{df['product_name'].nunique():,}"]
    ]
    t = Table(data, colWidths=[2.5*inch, 2.5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#6366f1')), 
        ('TEXTCOLOR', (0,0), (-1,0), colors.white), 
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), 
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
    ]))
    story.append(t)
    
    # 2. Visual Charts (NEW)
    if include_charts:
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Business Performance Visuals", heading_style))
        story.append(create_trend_chart(df))
        story.append(Spacer(1, 0.1*inch))
        story.append(create_top_products_chart(df))
    
    # 3. Top Products Table
    if include_products:
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Top Performing Products (Data Table)", heading_style))
        top = df.groupby('product_name')['total_value'].sum().sort_values(ascending=False).head(n_products)
        pdata = [['Rank', 'Product Name', 'Revenue generated']]
        for i, (n, v) in enumerate(top.items(), 1):
            pdata.append([str(i), str(n)[:40] + ('...' if len(str(n))>40 else ''), f"£{v:,.2f}"])
            
        pt = Table(pdata, colWidths=[0.5*inch, 4.0*inch, 1.5*inch])
        pt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#10b981')), 
            ('TEXTCOLOR', (0,0), (-1,0), colors.white), 
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
        ]))
        story.append(pt)

    # 4. Basket Analysis
    if include_basket and st.session_state.get('basket_rules') is not None and len(st.session_state['basket_rules']) > 0:
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("Market Basket Associations (Bundling Opportunities)", heading_style))
        rules = st.session_state['basket_rules'].head(10)
        
        bdata = [['When a customer buys...', 'They also buy...', 'Lift (Likelihood)']]
        for _, row in rules.iterrows():
            ant = ', '.join(list(row['antecedents']))[:30]
            cons = ', '.join(list(row['consequents']))[:30]
            bdata.append([ant, cons, f"{row['lift']:.1f}x"])
            
        bt = Table(bdata, colWidths=[2.5*inch, 2.5*inch, 1.0*inch])
        bt.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f59e0b')), 
            ('TEXTCOLOR', (0,0), (-1,0), colors.white), 
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
        ]))
        story.append(bt)

    # 5. AI Forecast
    if include_forecast and st.session_state.get('model_results') is not None:
        story.append(Spacer(1, 0.2*inch))
        story.append(Paragraph("AI Forecasting Model Performance", heading_style))
        
        results = st.session_state['model_results']
        story.append(Paragraph(f"<b>Champion Model Selected:</b> {results['champion_name']}", styles['Normal']))
        story.append(Spacer(1, 0.1*inch))
        
        fdata = [['Model Name', 'R² Score (Accuracy)', 'Mean Absolute Error']]
        for _, row in results['results_df'].iterrows():
            fdata.append([row['Model'], f"{row['R² Score']:.4f}", f"£{row['MAE']:,.2f}"])
            
        ft = Table(fdata, colWidths=[2.0*inch, 2.0*inch, 2.0*inch])
        ft.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#ec4899')), 
            ('TEXTCOLOR', (0,0), (-1,0), colors.white), 
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
        ]))
        story.append(ft)
    
    # Footer
    story.append(Spacer(1, 0.5*inch))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Paragraph("Confidential - Generated by SME Analytics Platform", ParagraphStyle('Footer', fontSize=8, textColor=colors.grey, alignment=TA_CENTER)))
    
    doc.build(story)
    buffer.seek(0)
    return buffer


if __name__ == "__main__":
    main()