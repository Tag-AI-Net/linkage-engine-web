import streamlit as st
import pandas as pd
import requests
import io

# --- CONFIGURATION ---
API_URL = "https://linkage-api-745046015036.us-east1.run.app/api/v1/link-datasets"
DEMO_KEY = "demo-public-key"
STRIPE_LINK1 = "https://buy.stripe.com/9B63cv0C1chVeib2ZM4Rq00"
STRIPE_LINK2 = "https://buy.stripe.com/00w14nacBeq37TN8k64Rq02"

st.set_page_config(page_title="Universal Linkage Engine", page_icon="🔗", layout="wide")

# --- SIDEBAR (MONETIZATION) ---
with st.sidebar:
    st.title("🔗 Get Full Access")
    st.markdown("The Universal Linkage Engine automates reconciliation between disparate data sets using empirical matching with LLM audits.")
    st.markdown("---")
    st.subheader("Pricing")
    st.markdown("**$50 per 5,000 total row records**")
    st.markdown("Pre-pay for up to 5,000 total records by row. Includes unlimited API access and integrations")
    st.markdown(f"[💳 Purchase Prepaid API Key]({STRIPE_LINK1})")
    st.markdown("**Metered Access at $0.01 per row**")
    st.markdown("Includes unlimited metered API access, integrations, and priority processing. A $5 monthly access fee applies.")
    st.markdown(f"[💳 Purchase Metered API Key]({STRIPE_LINK2})")
    st.markdown("---")
    st.markdown("*Note: If you do not enter an API key, the engine will run in Demo Mode and only process the first 20 rows of your datasets.*")

# --- UI FRONTEND ---
st.title("Universal Data Link Engine")
st.markdown("Securely upload your datasets and let the engine auto-detect and link matching records.")

# Authentication
api_key_input = st.text_input("API Key (Leave blank for 20-row Demo)", type="password")

# Data Upload
st.subheader("Upload Datasets")
col1, col2 = st.columns(2)
with col1:
    file_a = st.file_uploader("Upload Dataset A")
with col2:
    file_b = st.file_uploader("Upload Dataset B")

# Parameters
st.subheader("Linkage Parameters")
threshold = st.slider("Fuzzy Match Confidence Threshold", min_value=0.5, max_value=1.0, value=0.85, step=0.01)

# --- BACKEND LOGIC ---
if st.button("Link Datasets", type="primary"):
    if not file_a or not file_b:
        st.error("Please upload both datasets.")
    else:
        is_demo = not bool(api_key_input.strip())
        active_key = api_key_input.strip() if not is_demo else DEMO_KEY
        
        with st.spinner("Engine running... auto-mapping columns and linking records..."):
            try:
                # Handle Demo Truncation safely on the frontend
                if is_demo:
                    st.warning("⚠️ Running in Demo Mode: Only the first 20 rows will be processed.")
                    
                    # Read and truncate (Supporting CSV and Excel for the web demo)
                    try:
                        if file_a.name.endswith('.csv'): df_a = pd.read_csv(file_a).head(20)
                        else: df_a = pd.read_excel(file_a).head(20)
                        
                        if file_b.name.endswith('.csv'): df_b = pd.read_csv(file_b).head(20)
                        else: df_b = pd.read_excel(file_b).head(20)
                    except Exception:
                        st.error("Demo Mode currently supports CSV and Excel files. Please purchase an API key to process SPSS, Parquet, or JSON files.")
                        st.stop()
                    
                    # Convert truncated dataframes back to raw bytes for the API
                    buf_a, buf_b = io.BytesIO(), io.BytesIO()
                    df_a.to_csv(buf_a, index=False)
                    df_b.to_csv(buf_b, index=False)
                    
                    files = {
                        "file_a": ("demo_a.csv", buf_a.getvalue()),
                        "file_b": ("demo_b.csv", buf_b.getvalue())
                    }
                else:
                    # Paid user: Send the raw files directly to the server as-is
                    files = {
                        "file_a": (file_a.name, file_a.getvalue()),
                        "file_b": (file_b.name, file_b.getvalue())
                    }
                
                # Execute the API Call
                params = {"key": active_key}
                data = {"threshold": threshold}
                
                response = requests.post(API_URL, params=params, data=data, files=files)
                
                if response.status_code == 200:
                    try:
                        result_data = response.json()
                        linked_df = pd.DataFrame(result_data.get("matches", []))
                    except requests.exceptions.JSONDecodeError:
                        linked_df = pd.read_csv(io.StringIO(response.text))
                    
                    st.success(f"Linkage Complete! Found {len(linked_df)} matched records.")
                    st.dataframe(linked_df.head(10))
                    
                    csv_buffer = io.StringIO()
                    linked_df.to_csv(csv_buffer, index=False)
                    
                    st.download_button(
                        label="Download Merged Dataset",
                        data=csv_buffer.getvalue(),
                        file_name="linked_results.csv",
                        mime="text/csv"
                    )
                else:
                    st.error(f"API Error {response.status_code}: {response.text}")
                    
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")



def render_api_docs_sidebar():
    """Renders the comprehensive, technical API documentation inside the Streamlit sidebar."""
    st.sidebar.markdown("---")
    st.sidebar.subheader("🛠️ Developer & Integration Hub")
    
    with st.sidebar.expander("🔌 Universal Linkage API Documentation", expanded=False):
        st.markdown("""
        ### Overview
        The Universal Linkage Engine is a schema-agnostic, hybrid record linkage API. It automatically profiles disparate datasets to detect empirical overlaps, executes a cascading fuzzy-match strategy, and utilizes an integrated LLM to adjudicate ambiguous matches.
        
        It can return a finalized merged CSV or an **Actionable JSON** payload designed for webhooks and enterprise automation platforms.

        ---

        ### 1. Endpoint Configuration
        * **Method:** `POST`
        * **URL:** `https://linkage-api-745046015036.us-east1.run.app/api/v1/link-datasets`
        * **Payload Type:** `multipart/form-data`

        ---

        ### 2. Request Parameters
        
        | Parameter | Type | Required | Description |
        | :--- | :--- | :--- | :--- |
        | `file_a` | File | Yes | Primary source dataset (`.csv`, `.json`, `.parquet`, `.xml`, `.sav`, `.dta`, `.sas7bdat`). |
        | `file_b` | File | Yes | Target dataset to match against `file_a`. |
        | `key` | String | Yes | Your active metered or prepaid API key. |
        | `return_csv` | Boolean | No | Defaults to `true`. If `false`, returns structured JSON actions for database/CRM webhooks. |

        ---

        ### 3. Universal Trigger Schema (JSON Mode)
        When calling the API with `return_csv=false`, the server isolates the matching records and returns conditional `trigger_event` flags to let downstream workflows execute precise routing logic.

        **Example Response:**
        ```json
        {
          "status": "success",
          "summary": {
            "records_processed": 5420,
            "matches_found": 12
          },
          "actions": [
            {
              "trigger_event": "EXACT_DUPLICATE",
              "confidence_score": 100.0,
              "match_method": "Exact unique_id + last_name",
              "record_a_source": {
                "id_a": 1045,
                "system_id": "CRM-8821",
                "name": "Jon Doe"
              },
              "record_b_target": {
                "id_b": 22,
                "system_id": "WEB-991",
                "name": "Jonathan Doe",
                "email": "jon@example.com"
              }
            }
          ]
        }
        ```

        ---

        ### 4. Enterprise Automation Use Cases

        * **CRM Deduplication & Enrichment:** Set `return_csv=false`. Map your webhook trigger step: `IF trigger_event == 'EXACT_DUPLICATE'`, execute a step to automatically append missing fields found in `record_b_target` (like an updated email address) directly into the profile identified by `record_a_source.system_id`.
        * **Database Cleanup & Hygiene:** For building management systems or continuous directory audits, use the isolated tracking parameters. If an exact overlap or redundancy is flagged, your downstream workflow can instantly target and purge or archive `record_b_target.system_id` directly inside your secondary system without impacting the master source layer.
        * **Survey Frame Merging:** For matching standalone research frames (e.g., aligning voter registries with unmatched text-to-web or email-based field exit polling data), pass the files with `return_csv=true`. The engine handles cross-column semantic mapping automatically and delivers a clean data download instantly.
        """)

# Example usage within your main layout script:
# render_api_docs_sidebar()
