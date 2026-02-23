import pandas as pd
import streamlit as st
from streamlit_drawable_canvas import st_canvas

from Signature_utils import convert_canvas_to_image
from generateur_pdf import generate_pdf


def _canvas_has_strokes(canvas_result):
    if canvas_result is None or canvas_result.json_data is None:
        return False
    return len(canvas_result.json_data.get("objects", [])) > 0


@st.cache_data(show_spinner=False)
def _load_excel(file_bytes):
    return pd.read_excel(file_bytes)


st.set_page_config(layout="wide")
st.title("Emargement - Conseil National du Reseau CERFRANCE")
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
    </style>
    """,
    unsafe_allow_html=True,
)

##Selectionner le fichier excel et charger les données
uploaded_file = st.file_uploader("Selectionner le fichier Excel des reunions", type=["xlsx"])

#EXCEL_PATH = r"C:\Users\bboussari\OneDrive - CONSEIL NATIONAL CERFRANCE\Direction Digital\Bdd_reunion.xlsx"

if uploaded_file is not None:
    df = _load_excel(uploaded_file.getvalue())
    liste_reunions = df["Reunions"].unique().tolist()
    selected_meeting = st.selectbox("Choisir la reunion", liste_reunions)

    if selected_meeting:
        required_columns = {"Reunions", "Nom", "Poste", "Entreprise"}
        if not required_columns.issubset(df.columns):
            st.error("Colonnes attendues: Reunions, Nom, Poste, Entreprise.")
            st.stop()

        selected_rows = df[df["Reunions"] == selected_meeting]
        auto_show_day2 = True
        if "NbJours" in df.columns:
            auto_show_day2 = int(selected_rows["NbJours"].fillna(1).max()) >= 2
        elif "NombreJours" in df.columns:
            auto_show_day2 = int(selected_rows["NombreJours"].fillna(1).max()) >= 2

        show_day2_key = f"show_day2::{selected_meeting}"
        if show_day2_key not in st.session_state:
            st.session_state[show_day2_key] = auto_show_day2
        show_day2 = st.toggle("Reunion sur 2 jours", key=show_day2_key)

        meeting_state_key = f"meeting_state::{selected_meeting}"
        if meeting_state_key not in st.session_state:
            st.session_state[meeting_state_key] = {}
        meeting_state = st.session_state[meeting_state_key]

        participants_all_df = df[df["Reunions"] == selected_meeting][["Nom", "Poste", "Entreprise"]]

        for index, row in participants_all_df.iterrows():
            if index not in meeting_state:
                meeting_state[index] = {
                    "Nom": row["Nom"],
                    "Poste": row["Poste"],
                    "Entreprise": row["Entreprise"],
                    "Jour1": "Absent",
                    "Jour2": "Absent",
                    "CanvasVersion_Jour1": 0,
                    "CanvasVersion_Jour2": 0,
                    "Drawing_Jour1": None,
                    "Drawing_Jour2": None,
                    "Signature_Jour1": None,
                    "Signature_Jour2": None,
                }

        participants_df = participants_all_df.copy()
        st.subheader(f"Participants de la reunion : {selected_meeting}")
        search_name = st.text_input("Rechercher un participant par nom", key=f"search::{selected_meeting}")
        if search_name:
            participants_df = participants_df[
                participants_df["Nom"].astype(str).str.contains(search_name, case=False, na=False)
            ]
        st.caption(f"{len(participants_df)} participant(s) affiche(s)")

        for index, row in participants_df.iterrows():
            participant_state = meeting_state[index]
            if show_day2:
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 2])
            else:
                col1, col2, col3, col4 = st.columns([2, 2, 2, 2])
                col5 = None

            with col1:
                st.write(row["Nom"])
            with col2:
                st.write(row["Poste"])
            with col3:
                st.write(row["Entreprise"])

            key_j1 = f"{selected_meeting}_{index}_j1"
            if key_j1 not in st.session_state:
                st.session_state[key_j1] = participant_state["Jour1"]
            with col4:
                statut_j1 = st.radio(
                    f"Jour 1 - {row['Nom']}",
                    ["Present", "Absent", "Excuse"],
                    key=key_j1,
                )
            participant_state["Jour1"] = statut_j1

            if statut_j1 == "Present":
                st.write(f"Signature 1 {row['Nom']}:")
                canvas_key_j1 = (
                    f"canvas_j1_{selected_meeting}_{index}_{participant_state['CanvasVersion_Jour1']}"
                )
                canvas_j1 = st_canvas(
                    stroke_width=2,
                    stroke_color="black",
                    background_color="white",
                    height=150,
                    width=400,
                    display_toolbar=True,
                    initial_drawing=participant_state["Drawing_Jour1"],
                    key=canvas_key_j1,
                )
                if st.button("Recommencer J1", key=f"reset_j1_{selected_meeting}_{index}"):
                    participant_state["Drawing_Jour1"] = None
                    participant_state["Signature_Jour1"] = None
                    participant_state["CanvasVersion_Jour1"] += 1
                    st.rerun()
                # Autosave robuste: on met a jour uniquement si des traits existent.
                # Evite de perdre une signature a cause d'un rerun avec canvas vide.
                if _canvas_has_strokes(canvas_j1):
                    participant_state["Drawing_Jour1"] = canvas_j1.json_data
                    signature_j1 = convert_canvas_to_image(canvas_j1)
                    if signature_j1 is not None:
                        participant_state["Signature_Jour1"] = signature_j1
            else:
                participant_state["Drawing_Jour1"] = None
                participant_state["Signature_Jour1"] = None

            if show_day2:
                key_j2 = f"{selected_meeting}_{index}_j2"
                if key_j2 not in st.session_state:
                    st.session_state[key_j2] = participant_state["Jour2"]
                with col5:
                    statut_j2 = st.radio(
                        f"Jour 2 - {row['Nom']}",
                        ["Present", "Absent", "Excuse"],
                        key=key_j2,
                    )
                participant_state["Jour2"] = statut_j2

                if statut_j2 == "Present":
                    st.write(f"Signature 2 {row['Nom']}:")
                    canvas_key_j2 = (
                        f"canvas_j2_{selected_meeting}_{index}_{participant_state['CanvasVersion_Jour2']}"
                    )
                    canvas_j2 = st_canvas(
                        stroke_width=2,
                        stroke_color="black",
                        background_color="white",
                        height=150,
                        width=400,
                        display_toolbar=True,
                        initial_drawing=participant_state["Drawing_Jour2"],
                        key=canvas_key_j2,
                    )
                    if st.button("Recommencer J2", key=f"reset_j2_{selected_meeting}_{index}"):
                        participant_state["Drawing_Jour2"] = None
                        participant_state["Signature_Jour2"] = None
                        participant_state["CanvasVersion_Jour2"] += 1
                        st.rerun()
                    # Autosave robuste: on met a jour uniquement si des traits existent.
                    # Evite de perdre une signature a cause d'un rerun avec canvas vide.
                    if _canvas_has_strokes(canvas_j2):
                        participant_state["Drawing_Jour2"] = canvas_j2.json_data
                        signature_j2 = convert_canvas_to_image(canvas_j2)
                        if signature_j2 is not None:
                            participant_state["Signature_Jour2"] = signature_j2
                else:
                    participant_state["Drawing_Jour2"] = None
                    participant_state["Signature_Jour2"] = None
            else:
                participant_state["Jour2"] = "Absent"
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
            pdf_buffer = generate_pdf(selected_meeting, participants_data, include_day2=show_day2)
            st.success("PDF genere avec succes !")
            st.download_button(
                label="Telecharger le PDF",
                data=pdf_buffer.getvalue(),
                file_name=f"emargement_{selected_meeting}.pdf",
                mime="application/pdf",
            )
else:
    st.info("Charge un fichier Excel pour commencer.")
