"""
Streamlit UI Test for Schema Mapper (SILENT VERSION)

This version uses the silent schema mapper to avoid encoding issues.
Works on ALL systems including Windows CMD/PowerShell.

Run with: streamlit run test_streamlit_mapper_safe.py
"""

import streamlit as st
import pandas as pd

# ============================================================================
# IMPORT SILENT VERSION (NO ENCODING ISSUES)
# ============================================================================

from src.preprocessing.schema_mapper_silent import SchemaMapper

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="Schema Mapper Test",
    page_icon="🗺️",
    layout="wide"
)

# ============================================================================
# CACHED FUNCTIONS
# ============================================================================

@st.cache_data
def get_sample_data():
    """Load sample data (cached - only runs once)"""
    return pd.DataFrame({
        'OrderRef': ['A001', 'A002', 'A003', 'A004', 'A005'],
        'ItemCode': ['WIDGET-A', 'GADGET-B', 'THING-C', 'STUFF-D', 'WIDGET-A'],
        'ProductName': ['White Hanging Heart', 'Metal Lantern', 'Cream Cupid', 'Glass Star', 'White Hanging Heart'],
        'HowMany': [6, 6, 8, 6, 12],
        'SaleDate': ['2010-12-01', '2010-12-01', '2010-12-01', '2010-12-01', '2010-12-02'],
        'CostPer': [2.55, 3.39, 2.75, 3.25, 2.55],
        'BuyerID': ['CUST001', 'CUST001', 'CUST002', 'CUST001', 'CUST003'],
        'Location': ['United Kingdom', 'United Kingdom', 'France', 'United Kingdom', 'Germany']
    })

@st.cache_resource
def get_mapper(df):
    """Initialize mapper (cached)"""
    return SchemaMapper(df)

@st.cache_data
def get_auto_mapping(_mapper):
    """Run auto-detection (cached)"""
    return _mapper.auto_detect_mapping()

# ============================================================================
# MAIN APP
# ============================================================================

st.title("🗺️ Schema Mapper - Interactive Test")

st.markdown("""
This is a **live preview** of the column mapping interface.  
✨ **Silent version** - works perfectly on Windows!
""")

# ============================================================================
# STEP 1: SAMPLE DATA
# ============================================================================

st.header("📤 Step 1: Sample Data Upload")

st.info("💡 In the real app, users will upload their CSV here. For this test, we're using sample data.")

df_sample = get_sample_data()

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📊 Total Rows", len(df_sample))
with col2:
    st.metric("📋 Total Columns", len(df_sample.columns))
with col3:
    st.metric("🔴 Required Fields", "5")

st.dataframe(df_sample, use_container_width=True)

with st.expander("📊 Column Details"):
    st.write("**Your CSV columns:**")
    for i, col in enumerate(df_sample.columns, 1):
        st.write(f"{i}. `{col}` ({df_sample[col].dtype})")

# ============================================================================
# STEP 2: AUTO-DETECTION
# ============================================================================

st.header("🔍 Step 2: Auto-Detection")

st.info("🤖 The system automatically tries to match your columns to standard field names.")

mapper = get_mapper(df_sample)
auto_mapping = get_auto_mapping(mapper)

st.subheader("🎯 Detection Results")

detection_results = []
for canonical_name, detected_col in auto_mapping.items():
    schema_info = mapper.CANONICAL_SCHEMA[canonical_name]
    
    detection_results.append({
        'Field': canonical_name,
        'Required': '🔴 Yes' if schema_info['required'] else '🟡 No',
        'Auto-Detected': detected_col if detected_col else '❌ Not Found',
        'Status': '✅ Found' if detected_col else '⚠️ Manual'
    })

detection_df = pd.DataFrame(detection_results)
st.dataframe(detection_df, use_container_width=True, hide_index=True)

detected_count = sum(1 for v in auto_mapping.values() if v is not None)
total_count = len(auto_mapping)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("✅ Detected", f"{detected_count}/{total_count}")
with col2:
    st.metric("❌ Not Detected", total_count - detected_count)
with col3:
    required_mapped = sum(1 for k, v in auto_mapping.items() 
                          if v is not None and mapper.CANONICAL_SCHEMA[k]['required'])
    st.metric("🔴 Required Mapped", f"{required_mapped}/5")

# ============================================================================
# STEP 3: MANUAL MAPPING
# ============================================================================

st.header("🔧 Step 3: Manual Mapping")

st.info("""
**📝 Instructions:**
- 🔴 = **Required** field (must be mapped)
- 🟡 = **Optional** field (can be skipped)
- ✅ Auto-detected mappings are pre-selected
- 🔧 Use dropdowns to correct or complete the mapping
""")

mapping = {}

for canonical_name, schema_info in mapper.CANONICAL_SCHEMA.items():
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        required_badge = "🔴" if schema_info['required'] else "🟡"
        st.markdown(f"### {required_badge} {canonical_name.replace('_', ' ').title()}")
        
        with st.expander("ℹ️ Field Information"):
            st.write(f"**Description:** {schema_info['description']}")
            st.write(f"**Data Type:** `{schema_info['data_type']}`")
            st.write(f"**Common Names:**")
            for example in schema_info['examples'][:5]:
                st.write(f"  • {example}")
    
    with col2:
        auto_detected = auto_mapping.get(canonical_name)
        
        options = ["-- Not in my data --"] + df_sample.columns.tolist()
        
        if auto_detected and auto_detected in df_sample.columns:
            default_idx = options.index(auto_detected)
            help_text = f"✅ Auto-detected: {auto_detected}"
        else:
            default_idx = 0
            help_text = "⚠️ Not auto-detected - please select manually"
        
        selected = st.selectbox(
            f"Map to column:",
            options=options,
            index=default_idx,
            key=f"map_{canonical_name}",
            help=help_text,
            label_visibility="collapsed"
        )
        
        if selected != "-- Not in my data --":
            mapping[canonical_name] = selected
            
            with st.expander("👀 Preview selected column"):
                st.write(f"**Sample values from `{selected}`:**")
                st.write(df_sample[selected].head(3).tolist())
                st.write(f"**Data type:** `{df_sample[selected].dtype}`")
        else:
            mapping[canonical_name] = None
    
    st.markdown("---")

# ============================================================================
# STEP 4: VALIDATION
# ============================================================================

st.header("✔️ Step 4: Validation")

if st.button("🔍 Validate Mapping", type="primary", use_container_width=True):
    
    is_valid, errors = mapper.validate_mapping(mapping)
    
    if is_valid:
        st.success("✅ **Validation Passed!** All required fields are properly mapped.")
        
        with st.expander("📋 Final Mapping Summary"):
            mapping_summary = []
            for canonical, user_col in mapping.items():
                if user_col:
                    mapping_summary.append({
                        'Standard Field': canonical,
                        'Your Column': user_col,
                        'Required': '🔴' if mapper.CANONICAL_SCHEMA[canonical]['required'] else '🟡'
                    })
            
            st.dataframe(pd.DataFrame(mapping_summary), use_container_width=True, hide_index=True)
        
        if st.button("✨ Apply Mapping & Transform Data", type="primary"):
            
            df_transformed = mapper.apply_mapping(mapping)
            
            st.success("🎉 **Data Transformed Successfully!**")
            
            st.subheader("📊 Transformation Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**BEFORE (Your Columns)**")
                st.dataframe(df_sample, use_container_width=True)
                st.caption(f"Columns: {df_sample.columns.tolist()}")
            
            with col2:
                st.markdown("**AFTER (Standardized)**")
                st.dataframe(df_transformed, use_container_width=True)
                st.caption(f"Columns: {df_transformed.columns.tolist()}")
            
            st.balloons()
            
            csv = df_transformed.to_csv(index=False)
            st.download_button(
                label="📥 Download Transformed Data",
                data=csv,
                file_name="transformed_data.csv",
                mime="text/csv"
            )
    
    else:
        st.error(f"❌ **Validation Failed!** Found {len(errors)} error(s):")
        
        for error in errors:
            st.error(error)
        
        st.warning("⚠️ Please correct the errors above and try again.")

# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    st.header("📚 Help & Information")
    
    st.subheader("🎯 What is Schema Mapping?")
    st.write("""
    Schema mapping standardizes your CSV columns to a common format,
    allowing the analytics platform to process data from any source.
    """)
    
    st.subheader("🔴 Required Fields")
    required_fields = mapper.get_required_fields()
    for field in required_fields:
        st.write(f"• {field}")
    
    st.subheader("🟡 Optional Fields")
    optional_fields = mapper.get_optional_fields()
    for field in optional_fields:
        st.write(f"• {field}")
    
    st.subheader("💡 Tips")
    st.write("""
    - Auto-detection works best with standard column names
    - Check the preview to ensure correct mapping
    - Required fields must be mapped to proceed
    - Optional fields can be skipped
    """)
    
    st.subheader("🐛 Debug Info")
    with st.expander("Show Current Mapping"):
        st.json(mapping)