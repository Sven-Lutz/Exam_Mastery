"""Tiny synthetic lecture folder for the course-import tests (generated, public-safe; no real course material)."""
from pathlib import Path


def _pdf(path, pages, landscape=True):
    import pymupdf
    doc = pymupdf.open()
    w, h = (842, 595) if landscape else (595, 842)
    for title, lines, figure in pages:
        page = doc.new_page(width=w, height=h)
        page.insert_text((40, 60), title, fontsize=24)
        y = 110
        for line in lines:
            page.insert_text((50, y), line, fontsize=13)
            y += 22
        if figure:
            for i in range(8):  # a small bar chart: 8 distinct vector shapes = a figure that needs vision
                page.draw_rect(pymupdf.Rect(420 + 30 * i, 300, 445 + 30 * i, 300 + 20 * (i + 1)), color=(0, 0, 1), fill=(0.6, 0.7, 1))
    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(path)
    doc.close()


def make_course(root):
    root = Path(root)
    lec = root / "Vorlesung"
    _pdf(lec / "00 - Einführung.pdf", [
        ("Einführung in Entscheidungsprobleme", ["Organisation und Überblick über die Veranstaltung."], False),
        ("Lernziele", ["• Markov-Entscheidungsprozesse formal definieren können",
                       "• Bellman-Gleichungen für Wertfunktionen herleiten können",
                       "• Policy-Gradient-Schätzer erklären und anwenden können"], False),
        ("Rendite und Diskontierung", ["G_t = r_{t+1} + γ r_{t+2} + γ² r_{t+3} + …", "V(s) = E[G_t | S_t = s] mit γ ∈ [0,1)",
                                       "Q(s,a) = E[G_t | S_t = s, A_t = a]"], True)])
    _pdf(lec / "01 - Markov Entscheidungsprozesse.pdf", [
        ("Markov Entscheidungsprozesse", ["Zustände, Aktionen, Übergänge, Belohnungen."], False),
        ("Markov-Eigenschaft", ["Die Zukunft hängt nur vom aktuellen Zustand ab."], False),
        ("Übergangsmodell", ["P(s'|s,a) beschreibt die Dynamik der Umgebung."], True)])
    _pdf(lec / "02 - Dynamische Programmierung.pdf", [
        ("Dynamische Programmierung", ["Wertiteration und Politikiteration."], False),
        ("Bellman-Optimalität", ["V*(s) = max_a Σ P(s'|s,a) [r + γ V*(s')]"], False)])
    _pdf(lec / "04 - Policy Gradient.pdf", [
        ("Policy Gradient", ["Direkte Optimierung parametrisierter Politiken."], False),
        ("REINFORCE", ["∇J(θ) = E[∇ log π(a|s) G_t]", "Varianzreduktion mit Baseline b(s)"], True),
        ("Baselines", ["Eine Baseline verändert den Erwartungswert des Gradienten nicht."], False)])
    _pdf(lec / "05 - Actor Critic.pdf", [("Actor Critic", ["Kritiker schätzt die Wertfunktion."], False)])
    _pdf(root / "Übungen" / "Blatt 01 - Markov Entscheidungsprozesse.pdf", [
        ("Übungsblatt 1: Markov Entscheidungsprozesse", ["Aufgabe 1: Bestimmen Sie die Übergangsmatrix.",
                                                        "Aufgabe 2: Prüfen Sie die Markov-Eigenschaft."], False)], landscape=False)
    _pdf(root / "Übungen" / "Blatt 02 - Dynamische Programmierung.pdf", [
        ("Übungsblatt 2: Dynamische Programmierung", ["Aufgabe 1: Führen Sie zwei Schritte Wertiteration aus."], False)],
        landscape=False)
    _pdf(root / "Lösungen" / "Lösung Blatt 01.pdf", [
        ("Lösung zu Übungsblatt 1", ["Die Übergangsmatrix ist zeilenstochastisch."], False)], landscape=False)
    _pdf(root / "Klausur" / "Klausur 2024.pdf", [
        ("Klausur Entscheidungsprobleme 2024", ["Aufgabe 1 (Policy Gradient): Leiten Sie den REINFORCE-Schätzer her.",
                                               "Aufgabe 2 (Dynamische Programmierung): Wertiteration für ein MDP."], False)],
        landscape=False)
    (root / "Notizen.md").write_text("# Eigene Notizen\n\nBaselines reduzieren die Varianz.\n", encoding="utf-8")
    (root / "daten.xyz").write_bytes(b"\x00\x01binary")
    (root / ".DS_Store").write_bytes(b"\x00")
    (root / "04 - Policy Gradient.pdf").write_bytes((lec / "04 - Policy Gradient.pdf").read_bytes())  # loose duplicate
    return root
