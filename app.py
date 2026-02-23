import streamlit as st
from streamlit_drawable_canvas import st_canvas
from excel_loader import get_unique_reunions, get_participants_by_meeting
from generateur_pdf import generate_pdf
from Signature_utils import convert_canvas_to_image

from PIL import Image
import numpy as np

st.set_page_config(layout="wide")
st.title("Emargement- Conseil National du Réseau CERFRANCE")

# --- Étape 1 : Upload du fichier Excel ---
#uploaded_file = st.file_uploader("Sélectionner le fichier Excel des réunions", type=["xlsx"])
EXCEL_PATH = r"C:\Projet_Pennylane\Emargement\Bdd_reunion.xlsx"

if EXCEL_PATH is not None:

    # Charger les réunions uniques depuis le fichier
    df = get_unique_reunions() if False else None  # placeholder, on utilisera df directement
    df = __import__('pandas').read_excel(EXCEL_PATH)

    # Liste des réunions
    liste_reunions = df["Reunions"].unique().tolist()
    selected_meeting = st.selectbox("Choisir la réunion", liste_reunions)

    if selected_meeting:
        # Filtrer les participants pour cette réunion
        participants_df = df[df["Reunions"] == selected_meeting][["Nom", "Poste", "Entreprise"]]
        st.subheader(f"Participants de la réunion : {selected_meeting}")
        search_name = st.text_input("Rechercher un participant par nom")
        if search_name:
            participants_df = participants_df[
                participants_df["Nom"].astype(str).str.contains(search_name, case=False, na=False)
            ]
        st.caption(f"{len(participants_df)} participant(s) affiché(s)")

        participants_data = []

        # --- Étape 2 : Boucle sur les participants ---
        for index, row in participants_df.iterrows():
            col1, col2, col3, col4, col5 = st.columns([2,2,2,2,2])

            # Infos participant
            with col1:
                st.write(row["Nom"])
            with col2:
                st.write(row["Poste"])
            with col3:
                st.write(row["Entreprise"])

            # --- Jour 1 ---
            with col4:
                statut_j1 = st.radio(
                    f"Jour 1 - {row['Nom']}",
                    ["Présent", "Absent", "Excusé"],
                    key=f"{row['Nom']}_{index}_j1"
                )
            signature_j1 = None
            if statut_j1 == "Présent":
                st.write(f"Signature 1  {row['Nom']}:")
                canvas_j1 = st_canvas(
                    stroke_width=2,
                    stroke_color="black",
                    background_color="white",
                    height=150,
                    width=400,
                    key=f"canvas_j1_{row['Nom']}_{index}"
                )
                signature_j1 = convert_canvas_to_image(canvas_j1)

            # --- Jour 2 ---
            with col5:
                statut_j2 = st.radio(
                    f"Jour 2 - {row['Nom']}",
                    ["Présent", "Absent", "Excusé"],
                    key=f"{row['Nom']}_{index}_j2"
                )
            signature_j2 = None
            if statut_j2 == "Présent":
                st.write(f"Signature 2  {row['Nom']}:")
                canvas_j2 = st_canvas(
                    stroke_width=2,
                    stroke_color="black",
                    background_color="white",
                    height=150,
                    width=400,
                    key=f"canvas_j2_{row['Nom']}_{index}"
                )
                signature_j2 = convert_canvas_to_image(canvas_j2)

            participants_data.append({
                "Nom": row["Nom"],
                "Poste": row["Poste"],
                "Entreprise": row["Entreprise"],
                "Jour1": statut_j1,
                "Jour2": statut_j2,
                "Signature_Jour1": signature_j1,
                "Signature_Jour2": signature_j2
            })

        # --- Étape 4 : Bouton pour générer le PDF ---
        if st.button("Générer PDF"):
            pdf_buffer = generate_pdf(selected_meeting, participants_data)
            st.success("PDF généré avec succès !")
            st.download_button(
                label="Télécharger le PDF",
                data=pdf_buffer.getvalue(),
                file_name=f"emargement_{selected_meeting}.pdf",
                mime="application/pdf"
            )
