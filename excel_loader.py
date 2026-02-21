#charger les réunions et les participant depuis le fichiers excel 
import pandas as pd

EXCEL_PATH = r"C:\Projet_Pennylane\Emargement\Bdd_reunion.xlsx"

def load_data():
    """Charge la feuille unique."""
    df = pd.read_excel(EXCEL_PATH)
    return df

def get_unique_reunions():
    """Retourne la liste des réunions uniques."""
    df = load_data()
    return df["Reunion"].unique().tolist()

def get_participants_by_meeting(meeting_name):
    """Filtre les participants selon le nom de la réunion."""
    df = load_data()
    return df[df["Reunion"] == meeting_name][["Nom", "Poste", "Entreprise"]]