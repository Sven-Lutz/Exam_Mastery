# Designsystem v0.19 „Bühne“

## Verworfen (aus v0.17 „Papier & Tinte“)
| Entscheidung v0.17 | Problem in den Screenshots | Ersatz v0.19 |
|---|---|---|
| Cremefarbenes Papier (#f6f3ec) für alle Flächen | wirkte wie ein Dokument; Mathematik und Text ohne Unterschied | kühle neutrale Lesefläche + dunkle Bühne nur für Mathematik |
| Karten mit Rahmen und Schatten für jeden Block | „Card-Wüste“, viel vertikaler Platz, Formularcharakter | Gliederung durch Linien, Farbbalken, Typografie; Karten nur für Interaktion |
| Labs als lange Stapel (Vorhersage → Szene → Werkzeuge → Phasen) | Szene erst nach Formularen sichtbar; 5.000 px Seite | Skript links, Szene rechts (≥ 1180 px); auf dem Telefon Bühne oben |
| Lernstrecke in drei Spalten mit Seitenleiste | kleine Grafik, Lernpfad nahm eine Spalte | segmentierter Pfadbalken, große Bühne rechts |
| Versalien-Labels mit Sperrung (EXPERIMENT 01, SCHRITT 1 VON 12) | Template-Optik, schlecht lesbar | Satzschreibung, halbfett, Signalfarbe |
| Diagrammbeschriftungen 11 px | zu klein | ≥ 12,5 px auf der Bühne; Test: keine SVG-Schrift < 12 px |

## Neue Prinzipien
1. **Zwei Räume:** Lesen (hell, editorial, Serif) und Untersuchen (dunkle Bühne, leuchtende Rollenfarben, Mono-Zahlen). Die Bühne ist in hellem und dunklem Modus dunkel.
2. **Farbe = mathematische Rolle**, identisch in Szene, Formelband, Lernstrecke und Galerie; immer zusätzlich beschriftet.
3. **Diagnose steuert das Bild:** Die Bühne zeigt nach einer Antwort genau den betroffenen Teil (Pfad, Tiefpunkt, Thales-Kreis) – ohne die Lösung zu verraten.
4. **Progressive Disclosure:** Geführt zeigt einen Parameter mit Term, Wert, Gradient, Wirkung und Schritt-Delta; Erkunden alle Parameter, Gleichungen, Verlustverlauf, Finite-Differenzen-Prüfung.
5. **Evidenz sichtbar:** Jede Rückmeldung trägt ein Etikett, worauf sie beruht (numerisch, Stichprobe – kein Beweis, Rechenschritte, bekannter Fehler, nicht prüfbar).

## Designrichtungen (gerendert, `E2E_Nachweise/designrichtungen/`)
| Kriterium | A „Atlas“ (Editorial) | B „Bühne“ (Explorationsraum) |
|---|---|---|
| Eigenständigkeit | gut gesetzt, aber nah an bekannten Editorial-Layouts | klar unterscheidbar; Mathematik als Hauptobjekt |
| Wissenschaftliche Klarheit | sehr gut für Text und nummerierte Gleichungen | sehr gut für Modelle: Formelband + Grafik synchron |
| Hierarchie | Text dominiert, Grafik unter der Falz | Grafik und Aufgabe gleichzeitig sichtbar |
| Lesbarkeit langer Texte | stärker | schwächer (Skriptspalte schmaler) |
| Interaktion | konventionell | Schrittleiste, HUD, Fokuswechsel |
| Mobil | gut | gut (Bühne oben, Skript darunter) |
| Wartbarkeit | einfach | ein Token-Scope `.ds-stage` färbt alle bestehenden Szenen um |
**Wahl:** B für alle mathematischen Interaktionen, A-Regeln für Theorieseiten (keine Kästen, Lesemaß, Randkontext). Schriften unverändert (Source Serif 4 / Source Sans 3 / JetBrains Mono, OFL, offline).

## Geprüfte externe Ressourcen
- `frontend-design` (Anthropic): gelesen, nicht installiert; angewandt: Gegenstand-zuerst, Struktur muss Information tragen, keine Versalien-Template-Labels, ein Akzent statt vieler, Selbstkritik an Screenshots, Fokus/Reduced Motion/Mobil als Untergrenze.
- `webapp-testing` (Anthropic): Vorgehen übernommen (Python-Playwright, Aufklärung vor Aktion); die Engine hatte Playwright bereits.
- `skill-creator`: Eval-Fälle in v0.18 angelegt; in v0.19 keine Strukturänderung des Skills nötig.
- JSXGraph (LGPL/MIT), MathLive (MIT), jsPsych (MIT), manim (MIT), OATutor (MIT): nicht integriert – eigene SVG-Szenen decken die drei Fälle ab, Offline-Seiten bleiben ohne Fremdcode; manim erzeugt Videos, keine interaktiven Seiten. 3Blue1Brown-Lektionen dienten als Qualitätsmaßstab, keine Szene oder Gestaltung wurde übernommen.
