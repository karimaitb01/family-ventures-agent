"""Trie les pitch decks reçus et produit une fiche par dossier + un tableau de tri.

    python trier.py                       # tous les PDF de donnees/decks/
    python trier.py chemin/vers/deck.pdf  # un ou plusieurs decks précis

Résultats dans fiches/ : <deck>.md (fiche d'une page), <deck>.json (trace complète), tableau_de_tri.md.
"""

import argparse
import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

from tri.agent import analyser
from tri.fiche import RACINE, RECOMMANDATIONS, en_markdown, poids_criteres, score

FICHES = RACINE / "fiches"


def tableau(lignes: list[dict]) -> str:
    ordre = {r: i for i, r in enumerate(RECOMMANDATIONS)}
    lignes = sorted(lignes, key=lambda l: (ordre.get(l["reco"], 9), -l["score"]))
    sortie = ["# Tableau de tri", "",
              "| Dossier | Recommandation | Score | Grille notée | Alertes | Citations refusées | Fiche |",
              "|---|---|---|---|---|---|---|"]
    for l in lignes:
        sortie.append(f"| {l['nom']} | **{l['reco']}** | {l['score']}/100 | {l['couverture']} % | {l['alertes']} | "
                      f"{l['refus']} | [{l['deck']}.md]({l['deck']}.md) |")
    return "\n".join(sortie) + "\n"


async def principal(decks: list[Path]) -> None:
    FICHES.mkdir(exist_ok=True)
    poids, lignes = poids_criteres(), []
    for deck in decks:
        print(f"\n=== {deck.name} ===")
        r = await analyser(deck)
        (FICHES / f"{deck.stem}.json").write_text(json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8")
        if r["fiche"] is None:
            print(f"  ÉCHEC : pas de fiche valide ({r['cout']['statut']}). Dossier à trier à la main.")
            lignes.append({"nom": deck.stem, "reco": "À trier à la main", "score": 0, "couverture": 0,
                           "alertes": "-", "refus": len(r["refus"]), "deck": deck.stem})
            continue
        (FICHES / f"{deck.stem}.md").write_text(en_markdown(r["fiche"], r["faits"], poids, f"donnees/decks/{deck.name}",
                                                            r["cout"]), encoding="utf-8")
        note, couverture = score(r["fiche"]["criteres"], poids)
        lignes.append({"nom": r["fiche"]["nom"], "reco": r["fiche"]["recommandation"], "score": note,
                       "couverture": round(100 * couverture), "alertes": len(r["fiche"]["alertes"]),
                       "refus": len(r["refus"]), "deck": deck.stem})
        print(f"  → {r['fiche']['recommandation']}, {note}/100, {len(r['faits'])} faits vérifiés, "
              f"{len(r['refus'])} citations refusées, {r['cout']['cout_usd']} $")
    (FICHES / "tableau_de_tri.md").write_text(tableau(lignes), encoding="utf-8")
    print(f"\nTableau : {FICHES / 'tableau_de_tri.md'}")


if __name__ == "__main__":
    load_dotenv()
    parseur = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parseur.add_argument("decks", nargs="*", type=Path)
    args = parseur.parse_args()
    asyncio.run(principal(args.decks or sorted((RACINE / "donnees" / "decks").glob("*.pdf"))))
