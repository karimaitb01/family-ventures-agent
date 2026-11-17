"""Version HTML des fiches et du tableau de tri, pour les lire dans un navigateur (démo, partage)."""

from html import escape

from tri.fiche import score

COULEURS = {"Rencontrer": "#2E7D5B", "Creuser": "#C27A12", "Passer": "#A63D40"}

STYLE = """
:root { --encre:#1F2A44; --doux:#4A5670; --fond:#F4F6FA; --carte:#FFFFFF; --or:#B08D57; --ligne:#D8DEE9; }
* { box-sizing: border-box; }
body { margin:0; background:var(--fond); color:var(--encre); font:16px/1.5 Calibri, "Segoe UI", Arial, sans-serif; }
main { max-width:980px; margin:0 auto; padding:32px 20px 48px; }
h1 { font-family:Cambria, Georgia, serif; font-size:34px; margin:0; }
h2 { font-family:Cambria, Georgia, serif; font-size:21px; margin:28px 0 10px; }
.entete { display:flex; justify-content:space-between; align-items:flex-start; gap:24px; }
.entete > div:first-child { flex:1 1 auto; min-width:0; }
.score { flex:0 0 auto; }
.badge { display:inline-block; color:#fff; border-radius:999px; padding:4px 14px; font-weight:bold; font-size:15px; }
.score { text-align:right; }
.score b { font-family:Cambria, Georgia, serif; font-size:44px; line-height:1; }
.score small, .meta { color:var(--doux); font-size:14px; }
.carte { background:var(--carte); border-radius:10px; padding:16px 18px; box-shadow:0 1px 3px rgba(31,42,68,.08); }
table { width:100%; border-collapse:collapse; background:var(--carte); border-radius:10px; overflow:hidden; font-size:14px; }
th { background:var(--encre); color:#fff; text-align:left; padding:8px 10px; }
td { padding:8px 10px; border-top:1px solid var(--ligne); vertical-align:top; }
.note { white-space:nowrap; font-weight:bold; }
.points span { display:inline-block; width:11px; height:11px; border-radius:50%; background:var(--ligne); margin-right:3px; }
.points span.plein { background:var(--or); }
.cit { display:block; color:var(--doux); font-size:13px; margin-top:3px; }
.cit i { font-style:normal; background:#EEF1F6; border-radius:4px; padding:0 5px; margin-right:4px; color:var(--encre); font-weight:bold; }
.alerte { background:#FBEFEF; border-radius:10px; padding:12px 16px; margin-bottom:10px; }
.alerte b { color:#A63D40; }
ul, ol { margin:0; padding-left:22px; }
li { margin:4px 0; }
.pied { margin-top:28px; color:var(--doux); font-size:13px; font-style:italic; }
a { color:#1F5C99; }
@media (max-width:640px) { .entete { flex-direction:column; } .score { text-align:left; } h1 { font-size:28px; } }
"""


def _page(titre: str, corps: str) -> str:
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1"><title>{escape(titre)}</title>'
            f"<style>{STYLE}</style></head><body><main>{corps}</main></body></html>\n")


def _badge(reco: str) -> str:
    return f'<span class="badge" style="background:{COULEURS.get(reco, "#6B7A99")}">{escape(reco)}</span>'


def _preuves(ids: list[str], faits: dict) -> str:
    return "".join(f'<span class="cit"><i>p.{faits[i]["page"]}</i>« {escape(faits[i]["citation"])} »</span>'
                   for i in ids if i in faits)


def fiche_html(fiche: dict, faits: dict, poids: dict[str, int], source: str, cout: dict) -> str:
    note_100, couverture = score(fiche["criteres"], poids)
    lignes = []
    for nom, p in poids.items():
        v = fiche["criteres"][nom]
        if v["note"] == "inconnu":
            note = '<span class="note">inconnu</span>'
        else:
            points = "".join(f'<span class="{"plein" if k < v["note"] else ""}"></span>' for k in range(3))
            note = f'<span class="note points">{points}{v["note"]}/3</span>'
        lignes.append(f"<tr><td><b>{escape(nom.replace('_', ' '))}</b><br><small>poids {p}</small></td><td>{note}</td>"
                      f"<td>{escape(v.get('commentaire', ''))}{_preuves(v.get('faits', []), faits)}</td></tr>")
    alertes = "".join(f'<div class="alerte"><b>⚠ {escape(a["texte"])}</b>{_preuves(a["faits"], faits)}</div>'
                      for a in fiche.get("alertes", [])) or "<p>Aucune.</p>"
    manque = "".join(f"<li>{escape(m)}</li>" for m in fiche.get("informations_manquantes", [])) or "<li>Rien de notable.</li>"
    questions = "".join(f"<li>{escape(q)}</li>" for q in fiche.get("questions_fondateurs", []))
    associes = "".join(f"<li><b>{escape(a['nom'])}</b> : {escape(a['raison'])}</li>"
                       for a in fiche.get("associes_suggeres", [])) or "<li>Personne en particulier.</li>"
    corps = f"""
<div class="entete">
  <div><h1>{escape(fiche['nom'])}</h1>
    <p class="meta">{escape(fiche.get('secteur', '?'))} · {escape(fiche.get('stade', '?'))} · {escape(fiche.get('montant_recherche', '?'))}</p>
    {_badge(fiche['recommandation'])}</div>
  <div class="score"><b>{note_100}</b><small>/100</small><br><small>calculé sur {round(100 * couverture)} % de la grille</small></div>
</div>
<h2>En bref</h2><div class="carte">{escape(fiche.get('resume', ''))}</div>
<h2>Alertes</h2>{alertes}
<h2>Grille du fonds</h2>
<table><tr><th>Critère</th><th>Note</th><th>Justification et preuves dans le deck</th></tr>{''.join(lignes)}</table>
<h2>Ce que le deck ne dit pas</h2><div class="carte"><ul>{manque}</ul></div>
<h2>Questions à poser aux fondateurs</h2><div class="carte"><ol>{questions}</ol></div>
<h2>Associés du réseau à consulter</h2><div class="carte"><ul>{associes}</ul></div>
<p class="pied">Deck : {escape(source)}. Fiche préparée par un agent IA ({escape(str(cout.get('modele')))},
{cout.get('duree_s')} s). Chaque citation a été vérifiée mot pour mot dans le deck par le code ; le score est
calculé par le code. La décision reste à un humain. <a href="tableau_de_tri.html">Tableau de tri</a></p>"""
    return _page(f"{fiche['nom']} : {fiche['recommandation']}", corps)


def tableau_html(lignes: list[dict]) -> str:
    rangs = "".join(
        f"<tr><td><b>{escape(l['nom'])}</b></td><td>{_badge(l['reco'])}</td><td class='note'>{l['score']}/100</td>"
        f"<td>{l['couverture']} %</td><td>{l['alertes']}</td>"
        f"<td><a href='{escape(l['deck'])}.html'>ouvrir la fiche</a></td></tr>" for l in lignes)
    corps = f"""<h1>Tableau de tri</h1>
<p class="meta">Dossiers classés par recommandation puis par score. « Grille notée » : part des critères que le deck
permettait de juger (le reste est « inconnu »).</p>
<table><tr><th>Dossier</th><th>Recommandation</th><th>Score</th><th>Grille notée</th><th>Alertes</th><th>Fiche</th></tr>{rangs}</table>"""
    return _page("Tableau de tri", corps)
