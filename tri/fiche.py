"""Contrôle de la fiche rendue par l'agent, calcul du score et mise en page.

L'IA juge (notes, alertes, questions) ; le code vérifie et calcule. Le score n'est jamais
calculé par le modèle : c'est une somme pondérée faite ici, avec les poids de donnees/these.md.
"""

import json
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
THESE = RACINE / "donnees" / "these.md"
RESEAU = RACINE / "donnees" / "reseau.json"
RECOMMANDATIONS = ("Rencontrer", "Creuser", "Passer")
COUVERTURE_MIN_POUR_RENCONTRER = 0.5


def poids_criteres(these: str | None = None) -> dict[str, int]:
    """Lit la grille dans le tableau de these.md : « | critere | poids | ... | »."""
    these = these if these is not None else THESE.read_text(encoding="utf-8")
    return {m[1]: int(m[2]) for m in re.finditer(r"^\|\s*([a-z_]+)\s*\|\s*(\d+)\s*\|", these, re.M)}


def associes() -> list[str]:
    return [a["nom"] for a in json.loads(RESEAU.read_text(encoding="utf-8"))["associes"]]


def score(criteres: dict, poids: dict[str, int]) -> tuple[int, float]:
    """(score sur 100 calculé sur les critères connus, part de la grille effectivement notée)."""
    connus = {c: v["note"] for c, v in criteres.items() if v["note"] != "inconnu"}
    total = sum(poids.values()) * 3
    poids_connu = sum(poids[c] for c in connus) * 3
    if not poids_connu:
        return 0, 0.0
    return round(100 * sum(poids[c] * n for c, n in connus.items()) / poids_connu), poids_connu / total


def erreurs_fiche(fiche: dict, faits: dict, poids: dict[str, int], noms_associes: list[str]) -> list[str]:
    """Liste des problèmes à corriger. Vide = fiche acceptée."""
    err = []

    def faits_valides(ids, ou):
        if not ids:
            err.append(f"{ou} : aucun fait cité. Cite au moins un fait enregistré (F1, F2…).")
        for i in ids:
            if i not in faits:
                err.append(f"{ou} : le fait {i} n'existe pas. Enregistre-le d'abord avec noter_fait.")

    criteres = fiche.get("criteres", {})
    for nom in poids:
        if nom not in criteres:
            err.append(f"Critère « {nom} » manquant.")
    for nom, valeur in criteres.items():
        if nom not in poids:
            err.append(f"Critère « {nom} » inconnu de la grille.")
            continue
        note = valeur.get("note")
        if note not in (0, 1, 2, 3, "inconnu"):
            err.append(f"Critère « {nom} » : note {note!r} invalide (0, 1, 2, 3 ou « inconnu »).")
        elif note != "inconnu":
            faits_valides(valeur.get("faits", []), f"Critère « {nom} »")
    for k, alerte in enumerate(fiche.get("alertes", []), start=1):
        faits_valides(alerte.get("faits", []), f"Alerte {k}")
    for a in fiche.get("associes_suggeres", []):
        if a.get("nom") not in noms_associes:
            err.append(f"Associé « {a.get('nom')} » absent du réseau. Choisis un nom exact de la liste.")
    reco = fiche.get("recommandation")
    if reco not in RECOMMANDATIONS:
        err.append(f"Recommandation {reco!r} invalide : {', '.join(RECOMMANDATIONS)}.")
    if len(fiche.get("questions_fondateurs", [])) < 3:
        err.append("Donne au moins 3 questions à poser aux fondateurs.")

    # Garde-fous de décision : le modèle ne peut pas recommander une rencontre…
    if not err and reco == "Rencontrer":
        if criteres["adequation_these"]["note"] in (0, "inconnu"):
            err.append("« Rencontrer » refusé : le dossier n'est pas dans la thèse.")
        if score(criteres, poids)[1] < COUVERTURE_MIN_POUR_RENCONTRER:
            err.append("« Rencontrer » refusé : moins de la moitié de la grille est notée, le deck ne suffit pas.")
    return err


def en_markdown(fiche: dict, faits: dict, poids: dict[str, int], source: str, cout: dict) -> str:
    note_100, couverture = score(fiche["criteres"], poids)

    def citer(ids):
        return "<br>".join(f"{i} (p.{faits[i]['page']}) « {faits[i]['citation']} »" for i in ids if i in faits)

    lignes = [
        f"# {fiche['nom']} : {fiche['recommandation']}",
        "",
        f"**Score : {note_100}/100**, calculé sur {round(100 * couverture)} % de la grille (le reste est inconnu).  ",
        f"**Secteur** : {fiche.get('secteur', '?')} · **Stade** : {fiche.get('stade', '?')} · "
        f"**Montant recherché** : {fiche.get('montant_recherche', '?')}  ",
        f"**Deck** : `{source}`",
        "",
        "## En bref",
        fiche.get("resume", ""),
        "",
        "## Grille",
        "| Critère | Poids | Note | Justification | Preuves dans le deck |",
        "|---|---|---|---|---|",
    ]
    for nom, p in poids.items():
        v = fiche["criteres"][nom]
        note = "?" if v["note"] == "inconnu" else f"{v['note']}/3"
        lignes.append(f"| {nom} | {p} | {note} | {v.get('commentaire', '')} | {citer(v.get('faits', []))} |")
    lignes += ["", "## Alertes"]
    lignes += [f"- ⚠️ {a['texte']}  \n  Preuves : {citer(a['faits'])}" for a in fiche.get("alertes", [])] or ["- Aucune."]
    lignes += ["", "## Ce que le deck ne dit pas"]
    lignes += [f"- {m}" for m in fiche.get("informations_manquantes", [])] or ["- Rien de notable."]
    lignes += ["", "## Questions à poser aux fondateurs"]
    lignes += [f"{k}. {q}" for k, q in enumerate(fiche.get("questions_fondateurs", []), start=1)]
    lignes += ["", "## Qui, dans le réseau, peut aider à juger ce dossier"]
    lignes += [f"- **{a['nom']}** : {a['raison']}" for a in fiche.get("associes_suggeres", [])] or ["- Personne en particulier."]
    lignes += ["", "---",
               f"_Fiche préparée par un agent IA ({cout.get('modele')}, {cout.get('tours')} tours, "
               f"{cout.get('duree_s')} s, coût estimé {cout.get('cout_usd')} $). Chaque citation a été vérifiée mot pour mot "
               "dans le deck par le code ; le score est calculé par le code. La décision reste à un humain._", ""]
    return "\n".join(lignes)
