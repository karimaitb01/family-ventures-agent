"""Trie les pitch decks reçus et produit une fiche par dossier + un tableau de tri.

    python trier.py                                # tous les PDF de donnees/decks/
    python trier.py chemin/vers/deck.pdf           # un ou plusieurs decks précis
    python trier.py donnees/decks/verdalis.pdf --ouvrir   # ouvre la fiche dans le navigateur à la fin

Résultats dans fiches/ : <deck>.html et <deck>.md (fiche d'une page), <deck>.json (trace complète),
tableau_de_tri.html et tableau_de_tri.md (tous les dossiers déjà analysés).
"""

import argparse
import asyncio
import json
import webbrowser
from pathlib import Path

from dotenv import load_dotenv

from tri.agent import analyser
from tri.fiche import RACINE, RECOMMANDATIONS, en_markdown, poids_criteres, score
from tri.page import fiche_html, tableau_html

FICHES = RACINE / "fiches"


def lignes_du_tableau(poids: dict[str, int]) -> list[dict]:
    """Une ligne par dossier déjà analysé (fichiers fiches/*.json), triées par recommandation puis score."""
    lignes = []
    for trace in sorted(FICHES.glob("*.json")):
        r = json.loads(trace.read_text(encoding="utf-8"))
        if r["fiche"] is None:
            lignes.append({"nom": trace.stem, "reco": "À trier à la main", "score": 0, "couverture": 0,
                           "alertes": "-", "refus": len(r["refus"]), "deck": trace.stem})
            continue
        note, couverture = score(r["fiche"]["criteres"], poids)
        lignes.append({"nom": r["fiche"]["nom"], "reco": r["fiche"]["recommandation"], "score": note,
                       "couverture": round(100 * couverture), "alertes": len(r["fiche"]["alertes"]),
                       "refus": len(r["refus"]), "deck": trace.stem})
    ordre = {r: i for i, r in enumerate(RECOMMANDATIONS)}
    return sorted(lignes, key=lambda l: (ordre.get(l["reco"], 9), -l["score"]))


def tableau(lignes: list[dict]) -> str:
    sortie = ["# Tableau de tri", "",
              "| Dossier | Recommandation | Score | Grille notée | Alertes | Citations refusées | Fiche |",
              "|---|---|---|---|---|---|---|"]
    for l in lignes:
        sortie.append(f"| {l['nom']} | **{l['reco']}** | {l['score']}/100 | {l['couverture']} % | {l['alertes']} | "
                      f"{l['refus']} | [{l['deck']}.md]({l['deck']}.md) |")
    return "\n".join(sortie) + "\n"


async def principal(decks: list[Path], ouvrir: bool) -> None:
    FICHES.mkdir(exist_ok=True)
    poids, derniere = poids_criteres(), None
    for deck in decks:
        print(f"\n=== {deck.name} ===")
        r = await analyser(deck)
        (FICHES / f"{deck.stem}.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
        if r["fiche"] is None:
            print(f"  ÉCHEC : pas de fiche valide ({r['cout']['statut']}). Dossier à trier à la main.")
            continue
        source = f"donnees/decks/{deck.name}"
        (FICHES / f"{deck.stem}.md").write_text(en_markdown(r["fiche"], r["faits"], poids, source, r["cout"]),
                                                encoding="utf-8")
        derniere = FICHES / f"{deck.stem}.html"
        derniere.write_text(fiche_html(r["fiche"], r["faits"], poids, source, r["cout"]), encoding="utf-8")
        note, _ = score(r["fiche"]["criteres"], poids)
        print(f"  → {r['fiche']['recommandation']}, {note}/100, {len(r['faits'])} faits vérifiés, "
              f"{len(r['refus'])} citations refusées")
    lignes = lignes_du_tableau(poids)
    (FICHES / "tableau_de_tri.md").write_text(tableau(lignes), encoding="utf-8")
    (FICHES / "tableau_de_tri.html").write_text(tableau_html(lignes), encoding="utf-8")
    print(f"\nFiche : {derniere}\nTableau : {FICHES / 'tableau_de_tri.html'}")
    if ouvrir:
        webbrowser.open((derniere if len(decks) == 1 and derniere else FICHES / "tableau_de_tri.html").as_uri())


if __name__ == "__main__":
    load_dotenv()
    parseur = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parseur.add_argument("decks", nargs="*", type=Path)
    parseur.add_argument("--ouvrir", action="store_true", help="ouvre la fiche (ou le tableau) dans le navigateur")
    args = parseur.parse_args()
    asyncio.run(principal(args.decks or sorted((RACINE / "donnees" / "decks").glob("*.pdf")), args.ouvrir))
