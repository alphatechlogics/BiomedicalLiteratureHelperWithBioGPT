import torch
from transformers import set_seed
from transformers import BioGptTokenizer, BioGptForCausalLM

import streamlit as st
import datetime

# Merged utils.py content
biogpt_models = [
    "microsoft/biogpt",
    "microsoft/BioGPT-Large",
    "microsoft/BioGPT-Large-PubMedQA"
]

# Attempt to import sacremoses and handle ImportError
try:
    import sacremoses
except ImportError:
    st.error(
        "The 'sacremoses' package is required for BioGptTokenizer. Please install it using `pip install sacremoses`.",
        icon="🚨"
    )
    st.stop()


def check_min_max_seq_compatibility(min_slider_val, max_slider_val):
    if min_slider_val > max_slider_val:
        st.error(
            "Enter a minimum sequence length smaller than the maximum sequence length", icon="🚨"
        )


def check_input_predict(submit_state=False):
    if not submit_state:
        if not st.session_state.get("pred_in_text"):
            st.warning(
                "Make sure you have some input for text generation", icon="⚠️"
            )
    else:
        if not st.session_state.get("pred_in_text"):
            st.error("Please provide input text for generation", icon="🚨")
            st.stop()


@st.cache_resource
def setup_model(model_choice):
    tokenizer = BioGptTokenizer.from_pretrained(model_choice)
    model = BioGptForCausalLM.from_pretrained(model_choice)
    return tokenizer, model


def generate_text_from_model(model_choice, min_seq_val, max_seq_val, input_text):
    with st.spinner("Generating text..."):
        start_time = datetime.datetime.now()
        tokenizer, model = setup_model(model_choice)
        inputs = tokenizer(input_text, return_tensors="pt")

        set_seed(42)

        with torch.no_grad():
            beam_outputs = model.generate(
                **inputs,
                min_length=min_seq_val,
                max_length=max_seq_val,
                num_beams=5,
                num_return_sequences=1,  # Fixed to 1 to ensure only one answer is shown
                early_stopping=True
            )
        decoded_outputs = [
            tokenizer.decode(beam_output, skip_special_tokens=True) for beam_output in beam_outputs
        ]
        end_time = datetime.datetime.now()
        time_diff = (end_time - start_time).seconds
        return decoded_outputs, time_diff


# Initialize session state variables if not already present
if "pred_in_text" not in st.session_state:
    st.session_state["pred_in_text"] = ""

#### ---------------------STREAMLIT---------------------####

st.set_page_config(layout="wide")

# Main title
st.markdown(
    "<h1 align='center'>Biomedical Literature Helper with BioGPT</h1><br>",
    unsafe_allow_html=True
)

### ------BioGPT SECTION------###
st.header("BioGPT: Biomedical Text Generation and Mining")

# Container for BioGPT
biogpt_cont = st.container()
c1, c2 = biogpt_cont.columns((1, 2))

with biogpt_cont:
    with c1:
        st.subheader("Model Parameters")
        model_choice = st.selectbox(
            "Select Pre-trained Model", biogpt_models, index=0
        )

        min_slider = st.slider(
            label="Minimum Output Length",
            min_value=25,
            max_value=250,
            value=50,
            step=5,
            help="Set the minimum length for the generated text."
        )
        max_slider = st.slider(
            label="Maximum Output Length",
            min_value=50,
            max_value=2048,
            value=500,
            step=5,
            help="Set the maximum length for the generated text."
        )
        # Removed num_seq_slider and fixed number of sequences to 1

        st.markdown("### Input Text")
        pred_in_text = st.text_area(
            "Enter text for generation:",
            placeholder="e.g., Diabetes is",
            key="pred_in_text",
            height=150
        )

        # Buttons container
        submit_params = st.button(
            "Generate Text",
            type="primary",
            disabled=False  # Button remains enabled
        )

        check_min_max_seq_compatibility(min_slider, max_slider)

    with c2:
        st.markdown("### Generated Output")

        if submit_params:
            check_input_predict(submit_state=True)
            decoded_outputs, total_time = generate_text_from_model(
                model_choice=model_choice,
                min_seq_val=min_slider,
                max_seq_val=max_slider,
                input_text=st.session_state["pred_in_text"]
            )

            for idx, output in enumerate(decoded_outputs, 1):
                st.markdown(
                    f"**Answer #{idx}:**\n\n{output}"
                )

            st.success(f"Generated in {total_time} seconds.")
        else:
            check_input_predict()
            st.write("Awaiting input...")

# Optional: Add footer or additional information
st.markdown(
    "<hr><p style='text-align: center;'>© 2025 Biomedical Literature Helper with BioGPT</p>",
    unsafe_allow_html=True
)
