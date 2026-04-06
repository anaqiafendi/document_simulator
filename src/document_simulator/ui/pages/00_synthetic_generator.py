import streamlit as st

st.title("Synthetic Document Generator")
st.info(
    "The zone editor has moved to a dedicated React application. "
    "Start the API server with `uv run python -m document_simulator.api`, "
    "then open the link below."
)
st.markdown(
    "[Open Zone Editor \u2192](http://localhost:8000)",
    unsafe_allow_html=True,
)
