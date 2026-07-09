import streamlit as st
import pandas as pd
import requests
import io

# --- CONFIGURATION ---
API_BASE_URL = "https://linkage-api-745046015036.us-east1.run.app"
LEGACY_UPLOAD_URL = f"{API_BASE_URL}/api/v1/link-datasets"
DEMO_KEY = "demo-public-key"
STRIPE_LINK1 = "https://buy.stripe.com/9B63cv0C1chVeib2ZM4Rq00"
STRIPE_LINK2 = "https://buy.stripe.com/00w14nacBeq37TN8k64Rq02"

st.set_page_config(page_title="Universal Data Link Engine", page_icon="🔗", layout="wide")

# =================================================================
# HELPER FUNCTIONS (GCS ENTERPRISE PIPELINE)
# =================================================================
def get_gcs_ticket(api_key: str, filename: str) -> dict:
    """Step 1: Ask the backend for a secure Signed URL."""
    url = f"{API_BASE_URL}/api/v1/generate-upload-url"
    payload = {"filename": filename, "content_type": "application/octet-stream"}
    response = requests.post(url, params={"key": api_key}, json=payload)
    response.raise_for_status()
    return response.json()

def stream_to_gcs(signed_url: str, file_object):
    """Step 2: Stream the file directly to GCS in memory-safe 5MB chunks."""
    file_object.seek(0)
    headers = {"Content-Type": "application/octet-stream"}
    
    # Generator to yield chunks without loading the whole file into RAM
    def read_in_chunks(f, chunk_size=5 * 1024 * 1024):
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data

    response = requests.put(signed_url, data=read_in_chunks(file_object), headers=headers)
    response.raise_for_status()

def execute_gcs_linkage(api_key: str, path_a: str, path_b: str) -> str:
    """Step 3: Tell the backend to process files and return the Download URL."""
    url = f"{API_BASE_URL}/api/v1/link-gcs-datasets"
    payload = {
        "file_a_path": path_a,
        "file_b_path": path_b,
        "return_csv": True
    }
    response = requests.post(url, params={"key": api_key}, json=payload)
    response.raise_for_status()
    # Now expecting a JSON string containing the URL, not raw CSV bytes
    return response.json().get("download_url")

# =================================================================
# SIDEBAR (MONETIZATION & DOCUMENTATION)
# =================================================================
with st.sidebar:
    st.title("🔗 Get Full Access")
    st.markdown("The Universal Data Link Engine automates reconciliation between disparate data sets using empirical matching with LLM audits.")
    st.markdown("---")
    st.subheader("Pricing")
    st.markdown("**$50 per 5,000 total row records**")
    st.markdown("Pre-pay for up to 5,000 total records by row. Includes unlimited API access and integrations.")
    st.markdown(f"[💳 Purchase Prepaid API Key]({STRIPE_LINK1})")
    st.markdown("**Metered Access at $0.01 per row**")
    st.markdown("Includes unlimited metered API access, integrations, and priority processing. A $5 monthly access fee applies.")
    st.markdown(f"[💳 Purchase Metered API Key]({STRIPE_LINK2})")
    st.markdown("---")
    st.markdown("*Note: If you do not enter an API key, the engine will run in Demo Mode and only process the first 20 rows of your datasets.*")
    st.markdown("---")
    
    # Integrated Developer Hub Documentation
    st.subheader("🛠️ Developer Hub")
    with st.expander("🔌 Universal Data Link API Docs", expanded=False):
        st.markdown("""
        ### Overview
        The Universal Data Link Engine is a schema-agnostic, hybrid record Data Link API. It automatically profiles disparate datasets to detect empirical overlaps, executes a cascading fuzzy-match strategy, and utilizes an integrated LLM to adjudicate ambiguous matches.
        
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

# =================================================================
# UI FRONTEND
# =================================================================
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

# =================================================================
# BACKEND LOGIC PIPELINE
# =================================================================
if st.button("Link Datasets", type="primary"):
    if not file_a or not file_b:
        st.error("Please upload both datasets.")
    else:
        is_demo = not bool(api_key_input.strip())
        active_key = api_key_input.strip() if not is_demo else DEMO_KEY
        
        # ---------------------------------------------------------
        # ROUTE 1: DEMO MODE (Local Truncation to protect server)
        # ---------------------------------------------------------
        if is_demo:
            with st.spinner("Engine running in Demo Mode... auto-mapping columns and linking records..."):
                try:
                    st.warning("⚠️ Running in Demo Mode: Only the first 20 rows will be processed.")
                    
                    # Read and truncate safely
                    try:
                        if file_a.name.endswith('.csv'): df_a = pd.read_csv(file_a).head(20)
                        else: df_a = pd.read_excel(file_a).head(20)
                        
                        if file_b.name.endswith('.csv'): df_b = pd.read_csv(file_b).head(20)
                        else: df_b = pd.read_excel(file_b).head(20)
                    except Exception:
                        st.error("Demo Mode currently supports CSV and Excel files. Please purchase an API key to process SPSS, Parquet, or JSON files.")
                        st.stop()
                    
                    # Convert truncated dataframes back to bytes
                    buf_a, buf_b = io.BytesIO(), io.BytesIO()
                    df_a.to_csv(buf_a, index=False)
                    df_b.to_csv(buf_b, index=False)
                    
                    files = {
                        "file_a": ("demo_a.csv", buf_a.getvalue()),
                        "file_b": ("demo_b.csv", buf_b.getvalue())
                    }
                    
                    # Execute API Call to standard endpoint
                    params = {"key": active_key}
                    response = requests.post(LEGACY_UPLOAD_URL, params=params, files=files)
                    
                    if response.status_code == 200:
                        linked_df = pd.read_csv(io.StringIO(response.text))
                        st.success(f"Demo Linkage Complete! Found {len(linked_df)} matched records.")
                        st.dataframe(linked_df.head(10))
                        
                        csv_buffer = io.StringIO()
                        linked_df.to_csv(csv_buffer, index=False)
                        st.download_button(
                            label="Download Merged Dataset",
                            data=csv_buffer.getvalue(),
                            file_name="linked_demo_results.csv",
                            mime="text/csv"
                        )
                    else:
                        st.error(f"API Error {response.status_code}: {response.text}")
                        
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")

        # ---------------------------------------------------------
        # ROUTE 2: ENTERPRISE MODE (Direct-to-Cloud Uploads)
        # ---------------------------------------------------------
        else:
            try:
                with st.status("Executing Enterprise GCS Pipeline...", expanded=True) as status:
                    
                    # 1. Process File A
                    st.write("🎟️ Generating secure ticket for Dataset A...")
                    ticket_a = get_gcs_ticket(active_key, file_a.name)
                    st.write("☁️ Streaming Dataset A to Google Cloud...")
                    stream_to_gcs(ticket_a["upload_url"], file_a)
                    
                    # 2. Process File B
                    st.write("🎟️ Generating secure ticket for Dataset B...")
                    ticket_b = get_gcs_ticket(active_key, file_b.name)
                    st.write("☁️ Streaming Dataset B to Google Cloud...")
                    stream_to_gcs(ticket_b["upload_url"], file_b)
                    
                   # 3. Execute Match
                    st.write("🧠 Executing cascading fuzzy match engine (this may take a moment)...")
                    # Now returns a string URL, not massive bytes
                    download_url = execute_gcs_linkage(active_key, ticket_a["file_path"], ticket_b["file_path"])
                    
                    status.update(label="Pipeline Execution Complete!", state="complete", expanded=False)
                
                st.success("Successfully processed and matched records!")
                
                # Replace the memory-heavy download button with a direct link
                st.markdown(f"### [📥 Click Here to Download Merged Dataset]({download_url})")
                st.info("This secure link will expire in 1 hour. The original datasets have been purged from our servers for security.")

            except requests.exceptions.HTTPError as err:
                try:
                    error_detail = err.response.json().get("detail", err.response.text)
                except Exception:
                    error_detail = err.response.text
                st.error(f"API Error: {error_detail}")
            except Exception as e:
                st.error(f"System Error: {str(e)}")
