import math
from datetime import datetime
from io import BytesIO

import numpy as np
import pandas as pd
from PIL import Image as PILImage
import streamlit as st
from streamlit_drawable_canvas import st_canvas

from Signature_utils import convert_canvas_to_image
from generateur_pdf import generate_pdf

PRESENCE_OPTIONS = ["Present", "Absent", "Excuse"]
DEFAULT_STATUS = "Absent"


def _canvas_has_strokes(canvas_result):
    if canvas_result is None:
        return False
    if canvas_result.json_data is not None:
        if len(canvas_result.json_data.get("objects", [])) > 0:
            return True
    if canvas_result.image_data is not None:
        image = np.array(canvas_result.image_data)
        if image.size > 0:
            # Fond blanc => on detecte un trait si au moins un pixel est plus sombre que quasi-blanc.
            return bool(np.any(image[:, :, :3] < 245))
    return False


def _normalize_status(value):
    if value is None:
        return DEFAULT_STATUS
    v = str(value).strip().lower()
    if v in {"present", "présent", "prã©sent"}:
        return "Present"
    if v == "absent":
        return "Absent"
    if v in {"excuse", "excusé", "excusée"}:
        return "Excuse"
    return DEFAULT_STATUS


def _is_present(status):
    return _normalize_status(status) == "Present"


def _merge_signature_images(existing_image, new_image):
    if existing_image is None:
        return new_image
    if new_image is None:
        return existing_image

    existing_arr = np.array(existing_image.convert("RGB"), dtype=np.uint8)
    new_arr = np.array(new_image.convert("RGB"), dtype=np.uint8)

    if existing_arr.shape != new_arr.shape:
        height = max(existing_arr.shape[0], new_arr.shape[0])
        width = max(existing_arr.shape[1], new_arr.shape[1])
        existing_canvas = np.full((height, width, 3), 255, dtype=np.uint8)
        new_canvas = np.full((height, width, 3), 255, dtype=np.uint8)
        existing_canvas[: existing_arr.shape[0], : existing_arr.shape[1], :] = existing_arr
        new_canvas[: new_arr.shape[0], : new_arr.shape[1], :] = new_arr
        existing_arr = existing_canvas
        new_arr = new_canvas

    merged_arr = np.minimum(existing_arr, new_arr)
    return PILImage.fromarray(merged_arr, mode="RGB")


@st.cache_data(show_spinner=False)
def _load_excel(file_bytes):
    return pd.read_excel(BytesIO(file_bytes))


def _presence_selector(label, key):
    selected = st.segmented_control(
        label=label,
        options=PRESENCE_OPTIONS,
        selection_mode="single",
        key=key,
    )
    return _normalize_status(selected)


def _render_day_block(day_number, participant_state, selected_meeting, index, person_name, canvas_width):
    status_field = f"Jour{day_number}"
    draw_field = f"Drawing_Jour{day_number}"
    sign_field = f"Signature_Jour{day_number}"
    version_field = f"CanvasVersion_Jour{day_number}"
    status_key = f"{selected_meeting}_{index}_j{day_number}"

    if status_key not in st.session_state:
        st.session_state[status_key] = _normalize_status(participant_state.get(status_field))

    status = _presence_selector(f"Jour {day_number} - {person_name}", status_key)
    participant_state[status_field] = status

    if not _is_present(status):
        participant_state[draw_field] = None
        participant_state[sign_field] = None
        return

    st.caption(f"Signature J{day_number}")
    canvas_key = f"canvas_j{day_number}_{selected_meeting}_{index}_{participant_state[version_field]}"
    canvas_result = st_canvas(
        stroke_width=2,
        stroke_color="black",
        background_color="white",
        height=140,
        width=canvas_width,
        display_toolbar=True,
        update_streamlit=True,
        initial_drawing=participant_state[draw_field],
        key=canvas_key,
    )

    action_col1, action_col2 = st.columns([1, 1])
    with action_col1:
        if st.button(f"Enregistrer J{day_number}", key=f"save_j{day_number}_{selected_meeting}_{index}"):
            if _canvas_has_strokes(canvas_result):
                participant_state[draw_field] = canvas_result.json_data
                signature_image = convert_canvas_to_image(canvas_result)
                if signature_image is not None:
                    participant_state[sign_field] = _merge_signature_images(
                        participant_state.get(sign_field),
                        signature_image,
                    )
                    st.success(f"Signature J{day_number} enregistree")
            else:
                st.warning("Aucun trait detecte sur la signature.")
    with action_col2:
        if st.button(f"Recommencer J{day_number}", key=f"reset_j{day_number}_{selected_meeting}_{index}"):
            participant_state[draw_field] = None
            participant_state[sign_field] = None
            participant_state[version_field] += 1
            st.rerun()

    if participant_state.get(sign_field) is not None:
        st.caption(f"Signature J{day_number} sauvegardee")


st.set_page_config(layout="wide")
st.title("CNCER Sign")

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    [data-testid="stToolbar"] {display: none;}
    [data-testid="stStatusWidget"] {display: none;}
    [data-testid="stDecoration"] {display: none;}
    [data-testid="stSidebarNav"] {display: none;}

    div[data-testid="stSegmentedControl"] {
        background: #f4f7f9;
        border: 1px solid #d7dde4;
        border-radius: 12px;
        padding: 4px;
    }
    div[data-testid="stSegmentedControl"] button {
        border-radius: 9px !important;
        font-weight: 600 !important;
        border: none !important;
        color: #1f2937 !important;
        min-height: 34px !important;
    }
    div[data-testid="stSegmentedControl"] button[aria-pressed="true"] {
        color: #ffffff !important;
    }
    div[data-testid="stSegmentedControl"] button:nth-of-type(1)[aria-pressed="true"] {
        background: #16a34a !important; /* Present */
        box-shadow: 0 2px 8px rgba(22, 163, 74, 0.28);
    }
    div[data-testid="stSegmentedControl"] button:nth-of-type(2)[aria-pressed="true"] {
        background: #dc2626 !important; /* Absent */
        box-shadow: 0 2px 8px rgba(220, 38, 38, 0.28);
    }
    div[data-testid="stSegmentedControl"] button:nth-of-type(3)[aria-pressed="true"] {
        background: #7c3aed !important; /* Excuse */
        box-shadow: 0 2px 8px rgba(124, 58, 237, 0.28);
    }
    @media (max-width: 900px) {
        .block-container {
            padding-left: 0.7rem;
            padding-right: 0.7rem;
            padding-top: 0.6rem;
        }
        div[data-testid="stSegmentedControl"] button {
            min-height: 42px !important;
            font-size: 0.95rem !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

uploaded_file = st.file_uploader("Selectionner le fichier Excel des reunions", type=["xlsx"])

if uploaded_file is None:
    st.info("Chargez un fichier Excel pour commencer.")
    st.stop()

df = _load_excel(uploaded_file.getvalue())
required_columns = {"Reunions", "Nom", "Poste", "Entreprise"}
if not required_columns.issubset(df.columns):
    st.error("Colonnes attendues: Reunions, Nom, Poste, Entreprise.")
    st.stop()

liste_reunions = df["Reunions"].dropna().unique().tolist()
selected_meeting = st.selectbox("Choisir la reunion", liste_reunions)
if not selected_meeting:
    st.stop()

selected_rows = df[df["Reunions"] == selected_meeting]
auto_show_day2 = False
if "NbJours" in df.columns:
    auto_show_day2 = int(selected_rows["NbJours"].fillna(1).max()) >= 2
elif "NombreJours" in df.columns:
    auto_show_day2 = int(selected_rows["NombreJours"].fillna(1).max()) >= 2

toolbar_col1, toolbar_col2, toolbar_col3 = st.columns([2, 2, 2])
with toolbar_col1:
    show_day2_key = f"show_day2::{selected_meeting}"
    if show_day2_key not in st.session_state:
        st.session_state[show_day2_key] = auto_show_day2
    show_day2 = st.toggle("Reunion sur 2 jours", key=show_day2_key)
with toolbar_col2:
    compact_key = f"compact_mode::{selected_meeting}"
    if compact_key not in st.session_state:
        st.session_state[compact_key] = True
    compact_mode = st.toggle("Mode mobile/tablette", key=compact_key)
with toolbar_col3:
    page_size = st.selectbox("Participants par page", [5, 10, 20, 50], index=1, key=f"page_size::{selected_meeting}")

meeting_state_key = f"meeting_state::{selected_meeting}"
if meeting_state_key not in st.session_state:
    st.session_state[meeting_state_key] = {}
meeting_state = st.session_state[meeting_state_key]

participants_all_df = selected_rows[["Nom", "Poste", "Entreprise"]].copy()
participants_all_df = participants_all_df.sort_values(by=["Nom", "Entreprise"], na_position="last")

for index, row in participants_all_df.iterrows():
    if index not in meeting_state:
        meeting_state[index] = {
            "Nom": row["Nom"],
            "Poste": row["Poste"],
            "Entreprise": row["Entreprise"],
            "Jour1": DEFAULT_STATUS,
            "Jour2": DEFAULT_STATUS,
            "CanvasVersion_Jour1": 0,
            "CanvasVersion_Jour2": 0,
            "Drawing_Jour1": None,
            "Drawing_Jour2": None,
            "Signature_Jour1": None,
            "Signature_Jour2": None,
        }

st.subheader(f"Participants de la reunion : {selected_meeting}")
search_name = st.text_input("Rechercher un participant par nom", key=f"search::{selected_meeting}")
participants_df = participants_all_df.copy()
if search_name:
    participants_df = participants_df[
        participants_df["Nom"].astype(str).str.contains(search_name, case=False, na=False)
    ]

total_count = len(participants_df)
total_pages = max(1, math.ceil(total_count / page_size)) if total_count else 1
page_key = f"page::{selected_meeting}"
if page_key not in st.session_state:
    st.session_state[page_key] = 1
if st.session_state[page_key] > total_pages:
    st.session_state[page_key] = total_pages

page_col1, page_col2 = st.columns([3, 1])
with page_col1:
    st.caption(f"{total_count} participant(s) - page {st.session_state[page_key]}/{total_pages}")
with page_col2:
    st.number_input("Page", min_value=1, max_value=total_pages, step=1, key=page_key)

start = (st.session_state[page_key] - 1) * page_size
end = start + page_size
participants_page_df = participants_df.iloc[start:end]

for index, row in participants_page_df.iterrows():
    participant_state = meeting_state[index]
    name = row["Nom"]
    poste = row["Poste"]
    entreprise = row["Entreprise"]

    if compact_mode:
        header = f"{name} - {entreprise}"
        with st.expander(header, expanded=False):
            st.write(f"Poste: {poste}")
            _render_day_block(1, participant_state, selected_meeting, index, name, canvas_width=320)
            if show_day2:
                _render_day_block(2, participant_state, selected_meeting, index, name, canvas_width=320)
            else:
                participant_state["Jour2"] = DEFAULT_STATUS
                participant_state["Drawing_Jour2"] = None
                participant_state["Signature_Jour2"] = None
    else:
        if show_day2:
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
        else:
            col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
            col5 = None

        with col1:
            st.write(name)
        with col2:
            st.write(poste)
        with col3:
            st.write(entreprise)
        with col4:
            _render_day_block(1, participant_state, selected_meeting, index, name, canvas_width=290)
        if show_day2:
            with col5:
                _render_day_block(2, participant_state, selected_meeting, index, name, canvas_width=290)
        else:
            participant_state["Jour2"] = DEFAULT_STATUS
            participant_state["Drawing_Jour2"] = None
            participant_state["Signature_Jour2"] = None

participants_data = []
for index, _ in participants_all_df.iterrows():
    participant_state = meeting_state[index]
    participants_data.append(
        {
            "Nom": participant_state["Nom"],
            "Poste": participant_state["Poste"],
            "Entreprise": participant_state["Entreprise"],
            "Jour1": participant_state["Jour1"],
            "Jour2": participant_state["Jour2"],
            "Signature_Jour1": participant_state["Signature_Jour1"],
            "Signature_Jour2": participant_state["Signature_Jour2"],
        }
    )

if st.button("Generer PDF"):
    has_any_signature_j2 = any(p.get("Signature_Jour2") is not None for p in participants_data)
    include_day2_pdf = show_day2 and has_any_signature_j2
    pdf_buffer = generate_pdf(selected_meeting, participants_data, include_day2=include_day2_pdf)
    generation_date = datetime.now().strftime("%Y-%m-%d")
    safe_meeting_name = "".join(
        c if c.isalnum() or c in (" ", "-", "_") else "_" for c in str(selected_meeting)
    ).strip()
    st.session_state[f"pdf_bytes::{selected_meeting}"] = pdf_buffer.getvalue()
    st.session_state[f"pdf_name::{selected_meeting}"] = f"{safe_meeting_name}_{generation_date}.pdf"
    st.success("PDF genere avec succes !")

pdf_bytes_key = f"pdf_bytes::{selected_meeting}"
pdf_name_key = f"pdf_name::{selected_meeting}"
if pdf_bytes_key in st.session_state:
    st.download_button(
        label="Telecharger le PDF",
        data=st.session_state[pdf_bytes_key],
        file_name=st.session_state.get(pdf_name_key, "emargement.pdf"),
        mime="application/pdf",
        key=f"download_pdf::{selected_meeting}",
    )
