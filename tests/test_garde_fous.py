"""Tests des garde-fous (sans appel à l'IA) : python -m pytest -q"""

from pathlib import Path

import pytest

from tri.deck import citation_presente, lire_pages
from tri.fiche import associes, erreurs_fiche, poids_criteres, score

DECKS = Path(__file__).resolve().parent.parent / "donnees" / "decks"
POIDS = poids_criteres()


def fiche_valide(**surcharges):
    criteres = {c: {"note": 2, "faits": ["F1"], "commentaire": "ok"} for c in POIDS}
    fiche = {"nom": "X", "resume": "r", "criteres": criteres, "alertes": [], "informations_manquantes": [],
             "questions_fondateurs": ["a", "b", "c"], "associes_suggeres": [], "recommandation": "Creuser"}
    fiche.update(surcharges)
    return fiche


FAITS = {"F1": {"page": 1, "citation": "x", "fait": "x"}}


def test_grille_lue_dans_la_these():
    assert POIDS == {"adequation_these": 3, "equipe": 2, "traction": 2, "marche": 1, "levier_reseau": 2, "conditions": 1}


def test_citation_exacte_acceptee_meme_avec_casse_et_espaces():
    pages = lire_pages(DECKS / "verdalis.pdf")
    assert citation_presente(pages, 4, "ARR de 1,2 M€ en 2025")
    assert citation_presente(pages, 4, "arr  de 1,2 m€ en 2025")


@pytest.mark.parametrize("page,citation", [
    (4, "ARR de 2 M€ en 2025"),          # chiffre modifié
    (7, "ARR de 1,2 M€ en 2025"),        # mauvaise page
    (99, "ARR de 1,2 M€ en 2025"),       # page inexistante
    (4, "ARR"),                          # trop court pour prouver quoi que ce soit
])
def test_citation_inventee_ou_mal_placee_refusee(page, citation):
    assert not citation_presente(lire_pages(DECKS / "verdalis.pdf"), page, citation)


def test_fiche_valide_acceptee():
    assert erreurs_fiche(fiche_valide(), FAITS, POIDS, associes()) == []


def test_note_sans_preuve_refusee():
    f = fiche_valide()
    f["criteres"]["traction"] = {"note": 3, "faits": [], "commentaire": "super"}
    assert any("traction" in e for e in erreurs_fiche(f, FAITS, POIDS, associes()))


def test_fait_inexistant_refuse():
    f = fiche_valide(alertes=[{"texte": "t", "faits": ["F42"]}])
    assert any("F42" in e for e in erreurs_fiche(f, FAITS, POIDS, associes()))


def test_associe_invente_refuse():
    f = fiche_valide(associes_suggeres=[{"nom": "Bernard Arnault", "raison": "r"}])
    assert erreurs_fiche(f, FAITS, POIDS, associes())


def test_pas_de_rencontre_hors_these():
    f = fiche_valide(recommandation="Rencontrer")
    f["criteres"]["adequation_these"]["note"] = 0
    assert any("thèse" in e for e in erreurs_fiche(f, FAITS, POIDS, associes()))


def test_pas_de_rencontre_si_deck_trop_vide():
    f = fiche_valide(recommandation="Rencontrer")
    for c in ("equipe", "traction", "levier_reseau", "conditions"):
        f["criteres"][c] = {"note": "inconnu", "faits": [], "commentaire": ""}
    assert any("moitié" in e for e in erreurs_fiche(f, FAITS, POIDS, associes()))


def test_score_calcule_par_le_code():
    criteres = {c: {"note": 3} for c in POIDS}
    assert score(criteres, POIDS) == (100, 1.0)
    criteres["traction"] = {"note": "inconnu"}
    note, couverture = score(criteres, POIDS)
    assert note == 100 and couverture == pytest.approx(9 / 11)
