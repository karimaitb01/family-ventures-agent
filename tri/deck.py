"""Lecture du pitch deck et vérification des citations. Aucune IA ici : du code simple et testable."""

import re
import unicodedata
from pathlib import Path

from pypdf import PdfReader

LONGUEUR_MIN_CITATION = 6


def lire_pages(chemin: Path) -> list[str]:
    """Texte de chaque page du PDF (index 0 = page 1)."""
    return [page.extract_text() or "" for page in PdfReader(str(chemin)).pages]


def normaliser(texte: str) -> str:
    """Rend la comparaison insensible à la casse, aux espaces, aux apostrophes et aux puces."""
    texte = unicodedata.normalize("NFKC", texte).lower()
    for avant, apres in (("’", "'"), ("‘", "'"), ("«", '"'), ("»", '"'), ("“", '"'), ("”", '"'), ("•", " ")):
        texte = texte.replace(avant, apres)
    return re.sub(r"\s+", " ", texte).strip()


def citation_presente(pages: list[str], page: int, citation: str) -> bool:
    """Vrai si `citation` figure mot pour mot (après normalisation) à la page `page` (numérotée à partir de 1)."""
    if not 1 <= page <= len(pages):
        return False
    extrait = normaliser(citation)
    return len(extrait) >= LONGUEUR_MIN_CITATION and extrait in normaliser(pages[page - 1])


def texte_pour_agent(pages: list[str]) -> str:
    """Deck présenté à l'agent, page par page, pour qu'il puisse citer la bonne page."""
    return "\n\n".join(f"[Page {i}]\n{texte.strip()}" for i, texte in enumerate(pages, start=1))
