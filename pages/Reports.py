"""
Reports Page - PDF Generation
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER

st.set_page_config(page_title="Reports", page_icon="📄", layout="wide")

# --- RESPONSIVE CSS ---
st.markdown("""
<style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
        max-width: 100%;
    }
    
    /* Updated for Dark Mode visibility */
    [data-testid="stMetric"] {
        background-color: #262730; /* Darker background */
        border-radius: 10px;
        padding: 10px 15px;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


def main():
    st.title("📄 Report Generation")
    
    if st.session_state.get('data') is None:
        st.warning("⚠️ No data loaded. Please upload data from the Home page.")
        st.stop()
    
    df = st.session_state['data']
    
    st.markdown("---")
    
    # === REPORT OPTIONS ===
    st.markdown("### ⚙️ Report Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        include_products = st.checkbox("📦 Include Top Products", value=True)
        n_products = st.slider("Number of products", 5, 20, 10, disabled=not include_products)
    
    with col2:
        has_basket = st.session_state.get('basket_rules') is not None
        has_forecast = st.session_state.get('model_results') is not None
        
        include_basket = st.checkbox(
            "🛒 Include Basket Analysis",
            value=has_basket,
            disabled=not has_basket,
            help="Run basket analysis first to include"
        )
        
        include_forecast = st.checkbox(
            "🤖 Include AI Forecast",
            value=has_forecast,
            disabled=not has_forecast,
            help="Run model training first to include"
        )
    
    st.markdown("---")
    
    # === GENERATE BUTTON ===
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("📝 Generate PDF Report", type="primary", use_container_width=True):
            with st.spinner("Creating report..."):
                pdf = generate_pdf(
                    df,
                    include_products=include_products,
                    include_basket=include_basket,
                    include_forecast=include_forecast,
                    n_products=n_products
                )
                st.session_state['pdf_buffer'] = pdf
            st.success("✅ Report generated successfully!")
    
    # Download button
    if st.session_state.get('pdf_buffer'):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.download_button(
                "⬇️ Download PDF Report",
                st.session_state['pdf_buffer'],
                f"Sales_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                "application/pdf",
                use_container_width=True
            )
    
    st.markdown("---")
    
    # === PREVIEW ===
    st.markdown("### 👀 Report Preview")
    
    with st.expander("📊 Executive Summary", expanded=True):
        total_rev = df['total_value'].sum()
        total_orders = len(df)
        unique_products = df['product_name'].nunique()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("💰 Total Revenue", f"£{total_rev:,.2f}")
        col2.metric("🧾 Total Orders", f"{total_orders:,}")
        col3.metric("📦 Unique Products", f"{unique_products:,}")
        
        st.caption(f"Period: {df['order_date'].min().strftime('%Y-%m-%d')} to {df['order_date'].max().strftime('%Y-%m-%d')}")
    
    if include_products:
        with st.expander("📦 Top Products Preview"):
            top = df.groupby('product_name')['total_value'].sum().sort_values(ascending=False).head(n_products)
            st.dataframe(top.reset_index(), use_container_width=True, hide_index=True)
    
    if include_basket and has_basket:
        with st.expander("🛒 Basket Analysis Preview"):
            rules = st.session_state['basket_rules']
            st.caption(f"{len(rules)} association rules found")
            st.dataframe(rules.head(5)[['antecedents', 'consequents', 'lift']], use_container_width=True)
    
    if include_forecast and has_forecast:
        with st.expander("🤖 AI Forecast Preview"):
            results = st.session_state['model_results']
            st.caption(f"Champion model: {results['champion_name']}")


def generate_pdf(df, include_products, include_basket, include_forecast, n_products):
    """Generate comprehensive PDF report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch,
        leftMargin=0.5*inch,
        rightMargin=0.5*inch
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=24,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a5276'),
        spaceAfter=20
    )
    
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c3e50'),
        spaceBefore=20,
        spaceAfter=10
    )
    
    # === TITLE ===
    story.append(Paragraph("📈 Sales Analytics Report", title_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}",
        styles['Normal']
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a5276')))
    story.append(Spacer(1, 0.3*inch))
    
    # === EXECUTIVE SUMMARY ===
    story.append(Paragraph("Executive Summary", heading_style))
    
    total_rev = df['total_value'].sum()
    total_orders = len(df)
    unique_products = df['product_name'].nunique()
    avg_order = total_rev / total_orders if total_orders > 0 else 0
    
    summary_data = [
        ['Metric', 'Value'],
        ['Total Revenue', f"£{total_rev:,.2f}"],
        ['Total Orders', f"{total_orders:,}"],
        ['Average Order Value', f"£{avg_order:.2f}"],
        ['Unique Products', f"{unique_products:,}"],
        ['Period', f"{df['order_date'].min().strftime('%Y-%m-%d')} to {df['order_date'].max().strftime('%Y-%m-%d')}"]
    ]
    
    summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 0.3*inch))
    
    # === TOP PRODUCTS ===
    if include_products:
        story.append(Paragraph("Top Products", heading_style))
        
        top = df.groupby('product_name')['total_value'].sum().sort_values(ascending=False).head(n_products)
        
        prod_data = [['Rank', 'Product', 'Revenue']]
        for idx, (name, rev) in enumerate(top.items(), 1):
            prod_name = str(name)[:40] + ('...' if len(str(name)) > 40 else '')
            prod_data.append([str(idx), prod_name, f"£{rev:,.2f}"])
        
        prod_table = Table(prod_data, colWidths=[0.5*inch, 3.5*inch, 1.5*inch])
        prod_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#27ae60')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(prod_table)
        story.append(Spacer(1, 0.3*inch))
    
    # === BASKET ANALYSIS ===
    if include_basket and st.session_state.get('basket_rules') is not None:
        rules = st.session_state['basket_rules']
        
        story.append(Paragraph("Market Basket Insights", heading_style))
        
        basket_data = [['If Buys...', 'Also Buys...', 'Lift']]
        for _, row in rules.head(8).iterrows():
            ant = ', '.join([str(x)[:20] for x in list(row['antecedents'])])
            cons = ', '.join([str(x)[:20] for x in list(row['consequents'])])
            basket_data.append([ant[:30], cons[:30], f"{row['lift']:.1f}x"])
        
        basket_table = Table(basket_data, colWidths=[2*inch, 2*inch, 1*inch])
        basket_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        story.append(basket_table)
        story.append(Spacer(1, 0.3*inch))
    
    # === AI FORECAST ===
    if include_forecast and st.session_state.get('model_results') is not None:
        results = st.session_state['model_results']
        
        story.append(Paragraph("AI Forecasting Summary", heading_style))
        story.append(Paragraph(
            f"Champion Model: {results['champion_name']}",
            styles['Normal']
        ))
        
        model_data = [['Model', 'R² Score', 'MAE']]
        for _, row in results['results_df'].iterrows():
            model_data.append([
                row['Model'],
                f"{row['R² Score']:.4f}",
                f"£{row['MAE']:,.0f}"
            ])
        
        model_table = Table(model_data, colWidths=[2*inch, 1.5*inch, 1.5*inch])
        model_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9b59b6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(model_table)
    
    # === FOOTER ===
    story.append(Spacer(1, 0.5*inch))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 0.1*inch))
    
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.grey,
        alignment=TA_CENTER
    )
    story.append(Paragraph(
        "Generated by SME Analytics Platform | Confidential",
        footer_style
    ))
    
    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer


if __name__ == "__main__":
    main()
else:
    main()