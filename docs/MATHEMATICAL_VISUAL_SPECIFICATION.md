# Mathematical & Visual Quality Specification — v0.5 candidate

## Zweck und Geltungsbereich

Diese Spezifikation ergänzt die bestehende Engine; Bedienung bleibt `start '/lokaler/Vorlesungsordner'`. Keine neuen Agenten oder Orchestrierungsschichten. Vorhandene Rollen liefern überprüfbare Daten an die bestehenden Publisher. Historische Quell- und Produktdateien werden nicht umgeschrieben. Technische, modellgestützte fachliche und externe unabhängige Prüfung sind getrennte Nachweise.

## Ein gemeinsamer mathematischer Vertrag

Neue mathematische Inhalte verwenden `author.mathematics`. Jeder Datensatz enthält:

- global eindeutige `id`, `tex`, verständliche `alt`, `domain`, `assumptions`, exakte `source_refs`;
- `symbols`: Name, Bedeutung, Definitionsbereich und Einheit pro Symbol; `used_symbols` muss damit übereinstimmen. Skalare, Vektoren, Matrizen und Indizes werden ausdrücklich unterschieden;
- optional physikalische `dimension` als Exponentenvektor und deklarierte SymPy-Annahmen;
- optionale, begrenzte `checks` und für numerische Plots/Labs ein arithmetischer `expression`-Datensatz über denselben Symbolen.

Texte referenzieren `[[math:ID]]`, Querverweise `[[ref:ID]]`. Der Publisher nummeriert reproduzierbar. Keine unabhängigen Formelsatzkopien für Buch, Karte oder Labor. Alte Klartextunterstützung bleibt kompatibel, wird aber nicht als bestandene moderne Mathematikvalidierung ausgegeben.

Unterstützter Satz: AMS-ausgerichtete Gleichungen, mehrstufige Herleitungen, Matrizen/Vektoren, Summen, Integrale, Grenzwerte, Optimierungsnotation, Fallunterscheidungen und Beweisschritte. Chemische Notation über mhchem; Einheiten aufrecht. Finanzielle Variablen benötigen Bezugsperiode/Währung; statistische Darstellungen unterscheiden Daten, Schätzung und Unsicherheit. Mathematische Beweise brauchen Voraussetzungen, Argumentationsschritte und gegebenenfalls gesonderte Randfälle; ein Satzbild ist kein Beweis.

Offline-Renderer: eingefrorenes MathJax 3.2.2, SVG-Pfade ohne externe Fonts/CDN oder Laufzeit-JavaScript in Anki. Das neue Laufzeitverzeichnis ist von v0.4 getrennt. SVG ist die kanonische Satzdatei; Gleichungen stehen im PDF als eigenständig vermessene Vektorblöcke direkt im Text sowie in den Referenztafeln. Anki erhält hochauflösende Ableitungen desselben SVG. Dadurch wird native MathJax-Verfügbarkeit im Anki-Client nicht vorausgesetzt; die native Darstellung muss trotzdem tatsächlich geprüft werden. PNG/SVG und Quellen-/Rendererhashes werden aufbewahrt.

Unbekannte TeX-Befehle/Renderfehler, undefinierte Formelreferenzen, doppelte IDs, fehlende Symboldefinitionen/Einheiten und unsichere externe oder makrodefinierende Befehle scheitern ausdrücklich. Die lexikalische Symbolprüfung unterstützt deklarierte lateinische Grundsymbole und benannte griechische Variablen; aufrechte Einheiten, Text und Zahlenmengen werden getrennt. Für Transposition ist `\top` eindeutig; anders geschriebene Operatorsymbole müssen ausdrücklich erklärt werden. Diese Prüfung ist keine universelle semantische TeX-Analyse.

## Mathematische Prüfverfahren

Arithmetische Ausdrucksdaten werden über eine begrenzte AST-Grammatik in SymPy aufgebaut, ohne `eval`, `sympify` oder unsicheres `parse_expr` auf Quelltext. Unterstützt sind deklarierte Skalarsymbole, Zahlen, + − × ÷, begrenzte konstante Potenzen sowie sin/cos/exp/log/sqrt/Abs. Unbekannte Syntax scheitert; nicht unterstützte Operationen erhalten keinen behaupteten Prüfpass.

- Äquivalenz: symbolische Differenzvereinfachung unter expliziten Symbolannahmen.
- Numerische Referenzen: vollständige Substitution, endliche Ergebnisse und Toleranzprüfung; Rand- und degenerierte Fälle müssen in geeigneten Fällen explizit geprüft werden.
- Dimensionen: Exponentenvektoren für unterstützte Summen, Produkte, Quotienten und konstante Potenzen. Additionen erfordern gleiche Dimensionen. Diese Prüfung ersetzt keine Einheitenumrechnung oder fachliche Interpretation.
- Matrixbeweise, allgemeine Grenzwertbeweise, chemische Gültigkeit und statistische Identifikation sind nicht durch diese skalare AST-Prüfung zertifiziert. Quelle, Herleitung und gerendertes Produkt brauchen Begutachtung.

Die Existenz einer prüfbaren Nebenrechnung beweist nicht jede Aussage im gleichen Text. Numerische Beispiele ersetzen keinen allgemeinen Beweis.

## Fachadaptives Visual Engineering

Der Learning Designer entscheidet pro Kompetenz, ob eine Grafik erforderlich oder deutlich hilfreicher ist, mit begründetem `visual_decisions`-Datensatz. Erforderliche IDs müssen unter tatsächlich erzeugten Visualisierungen vorkommen. Reine `visual_description`-Prosa zählt nicht als erzeugte Abbildung.

Verbindliche gemeinsame Felder: stabile ID, Typ, Titel, vollständige Bildunterschrift, Textalternative, genaue Quellen und `data_origin` als source/synthetic/inference. Modellgenerierte Daten müssen ausdrücklich gekennzeichnet sein. Originaldateien bleiben unverändert. Eine Wiederverwendung fremder Originalgrafiken setzt belegte Zulässigkeit voraus; die Engine erfindet keine Rechtefreigabe. Nicht freigegebene Quellen werden nicht als lizenzierte Assets ausgegeben.

Unterstützte Vektortypen:

- Funktionsplots aus kanonischer Formel-ID, Variable, Intervall und festen Parametern. Eine andere Formel für den Plot ist nicht zulässig.
- Statistische Scatter-/Linien-/Balken-/Histogramm-/Fehlerbalkendarstellung aus deklarierten Datenreihen. Labels, Einheiten, Skalen und Legende sind Pflicht. Fehlerbalken werden nicht ohne Beleg zu Konfidenzintervallen erklärt.
- Algorithmen, Architekturen, Entscheidungs-/Prozessdiagramme, juristische Prüfungsschemata und Strukturübersichten aus begrenzten beschrifteten Graphen. Entscheidungen/Prüfschemata benötigen beschriftete Bedingungen.
- Zeitachsen mit zeitlich sortierten Ereignissen und Zeitmaß; Tabellen mit rechteckigen, tatsächlich gerenderten Inhalten.

Plots entstehen reproduzierbar in Matplotlib-SVG, Schemata in deterministischem SVG. PDF nutzt den Vektor, Web dieselbe SVG-Datei, Anki bei begründetem `figure_ids`-Bezug eine abgeleitete Datei mit Caption/Alt. Serien, Achsen und Parameter bleiben im QA-Datensatz. Unendliche Werte, unzulässige Log-Werte, falsche Unsicherheitslängen, ungültige Kanten und zu dichte Diagramme scheitern. Dichte Grafiken müssen aufgeteilt werden; winzige Schrift ist kein Ersatz.

## Editorial Design

Ein kohärentes Farbsystem, lokale Fonts und gemeinsame Abstände bleiben Grundlage. `presentation_mode` wählt nach der Lernoperation unterschiedliche Lesemuster:

- quantitativ: Intuition, Formalisierung, Beispiel, nummerierte Formeln mit Voraussetzungen/Symbolen;
- Regelfall: Sachverhalt/Frage, Maßstab und Anwendung, begründetes Ergebnis;
- experimentell: Beobachtung/Frage, Methode und Unsicherheit, Analyse/Interpretation;
- algorithmisch: Problem/Invariante, Verfahren/Begründung, Ausführungsspur.

Diese Muster legitimieren keine erfundene juristische oder wissenschaftliche Autorität. Bildunterschriften und Quellen bleiben sichtbar. Wiederholte Rubric-Köpfe und explizite Folgefehlerregeln bleiben erhalten. Formelbreite darf keine ganze Mobilseite sprengen; lange Formeln brauchen einen zugänglichen lokalen Scrollbereich oder Zerlegung. Vollständige menschliche Satzabnahme bleibt ein eigener Nachweis.

## Quality Gates und Grenzen

Automatische Prüfungen untersuchen Vertrags-/TeX-Syntax, Formelverweise, Symboldeklarationen, unterstützte Äquivalenzen/Referenzwerte/Dimensionen, kanonische Assetidentität über Ausgabekanäle, Lab-/Formelausdruck und echte Grafikdateien. Browserprüfungen laden tatsächliche Bilder und Karten, prüfen Reflow und Interaktionspfade. Geometrische Plotprüfungen beziehen sichtbare Achsenlabels ein; außerhalb des Achsintervalls unsichtbare Locator-Ticks sind kein Clippingfehler.

Alle Produkt-PDF-Seiten werden rasterisiert und in begrenzten Bildpaketen tatsächlich begutachtet. Relevante Originalquellen werden zusätzlich zum tatsächlichen Seiteninhalt bereitgestellt, soweit ihre Anker auf den Seiten auffindbar sind; fehlende Evidenz muss als Grenze im Audit stehen. Inhaltsrollen prüfen vor Veröffentlichung die vollständigen Quellen und strukturierten Inhalte. Keine dieser Modellprüfungen ist eine externe unabhängige Fachprüfung.

Native Anki-Desktop-/Mobiltests zählen nur nach realer Ausführung. Die v0.4.1-Blocker, die historische Migrationsgrenze, die externe Fachprüfung und der nicht geprüfte direkte Work-UI-Start werden weitergeführt. Kein GO bei offenen Pflichtgates. Ein demonstrierter Codepfad oder ein selbst verfasster Benchmark ersetzt keinen vollständigen echten Produktionslauf.

## Reproduzierbarkeit

Der Sprint bewahrt Quellcode, Quellenhashes, Versions-/Paketstände, Ausgabedateien, Screenshots, Rasterbilder, ungültige Antworten, fehlgeschlagene Versuche und Nachprüfungen. Die bisherigen 52 Testmethoden bleiben unverändert. Kontrastierende bekannte Beispiele werden zusätzlich getestet. Vorher-/Nachher-Benchmarks sind klar als deterministisch redaktionell verfasst gekennzeichnet und werden von tatsächlichen Codex-Produktionsläufen getrennt.

## Konkret ausgeführte Integritäts- und Lesbarkeitsgates

Die Autorenvalidierung prüft TeX tatsächlich im Renderer und sammelt Symbol- und Renderfehler für denselben begrenzten Korrekturversuch. Ein gültiges TeX-Satzbild bleibt von mathematischer Wahrheit getrennt. Die kanonischen SVG-Dateien und deren PNG-Ableitungen sind durch Hash-Provenienz verknüpft; veränderte Caches werden abgewiesen. Häufige TeX-Quellen werden innerhalb eines Prozesses wiederverwendet, nicht als unvalidierte Bilder übernommen.

Breite Formeln, Diagramme und Lab-Kurven erhalten lokale, per Tastatur erreichbare Scrollbereiche statt unleserlicher Schrumpfung oder Seitenüberlauf. Lab-Kurven besitzen benannte Achsen und eine Legende; konstante Antworten erhalten eine endliche Achsenspanne. Die wissenschaftlichen Plotfonts sind in SVG-Pfade umgewandelt.

Histogramme verwenden rohe `series.values`, eine explizite Bin-Anzahl (2–20) und dimensionslose Häufigkeiten. Tatsächliche Häufigkeiten und Grenzen werden im QA-Datensatz aufbewahrt; vorhandene y-Werte werden nicht stillschweigend ignoriert.

Die Fach-/Didaktikaudits vor Veröffentlichung beurteilen Quellen, Inhalte und Grafikdaten. Der fehlende Bildnachweis in dieser Phase bleibt unverified, ist aber kein Beweis, dass der spätere Export fehlt. Die nachgelagerte technische und visuelle Prüfung muss tatsächliche Dateien nachweisen und fehlende erforderliche Bilder weiterhin ablehnen.

## Nachweis aus dem vollständigen Echtprodukt: Lösungen und portable Zeichen

- Lösungsobjekte können `figure_ids` auf exakt passende vorhandene `learning_plan.visuals` enthalten. Referenzen werden gegen die expliziten IDs geprüft; der Publisher bettet dieselbe echte SVG-Grafik im Lösungsabschnitt von PDF und Web ein. Es gibt keine automatische Identitätsableitung aus ähnlichem Inhalt. Unbekannte IDs und nicht ersetzte Grafikplätze sind FAIL.
- Der Solutions-Auftrag bekommt den bestehenden Visualisierungsplan und nutzt kanonische Mathematikverweise. Textbasierte wissenschaftliche Plots mit Koordinatenzeilen und Zeichenmarkern werden abgewiesen; reguläre numerische Tabellen bleiben erlaubt. Eine notwendige Grafik mit abweichenden Daten muss als Lücke sichtbar bleiben.
- Unicode-Ziffernindizes und -exponenten in einfacher Prosa werden zu typografischen Indizes normalisiert. Lokal installierte DejaVu-Schriften werden verwendet; keine Schriftdateien werden im Engine-Release verteilt. Das tatsächliche PDF-Gate prüft fehlende `.notdef`-Glyphen.
- Auch Tabellen-, Diagramm- und Kantenbeschriftungen werden aus dem fest gewählten lokalen Font in echte Vektorpfade umgesetzt. Ein expliziter Zeichensatzcheck verwirft nicht unterstützte Glyphen vor dem Export. Titel, Textalternativen und Labeltexte bleiben als SVG-Metadaten erhalten. Dies vermeidet die im Echtprodukt beobachtete abweichende Ersatzschrift bei SVG→PDF. Komplexe Schriftsysteme und vollständige Screenreader-Bedienung sind damit nicht allgemein abgenommen.

Diese Regeln wurden durch konkrete FAILs an der echten Statistik-Musterlösung und einem fehlenden Gradientenzeichen begründet; sie sind Teil der regulären Pipeline und nicht nur lokale Nachbearbeitung. Ein separat gekennzeichneter Nachsatz gespeicherter Modellergebnisse ist dennoch kein frischer vollständiger Produktionsnachweis.

### Gerichtete Kanten und Zeitdarstellung

Pfeilspitzen werden als explizite gefüllte SVG-Polygone gezeichnet. Importerabhängige SVG-Marker sind kein ausreichender PDF-Nachweis. Eine tatsächliche PDF-Zeichenprüfung muss alle Spitzen einschließlich Rückkante erhalten. Ereignisdiagramme zeigen eine geordnete Chronologie; Caption, Alternative und SVG-Beschreibung kennzeichnen, dass die vertikalen Abstände keine proportionale Zeitachse darstellen. Proportionale Zeitachsen werden nicht behauptet.

### Quellenprüfung von Domänen und Transfergrafiken

Endliche Referenzdaten sind ausdrücklich ausgewählte Beispiele und dürfen keine unqualifizierte Einschränkung einer weiter gefassten Lab-/Modelldomäne behaupten. Autoren- und Auditaufträge verlangen einen zulässigen Kontrollwert außerhalb der aufgeführten Referenzen. Konstruktive Transferaufgaben mit neuen Fällen/Daten benötigen exakt passende deklarative Lösungsgrafiken; fehlende notwendige Spezifikationen sind vor Publikation ein inhaltlicher Mangel. Fehlende fertige Bilddateien vor der Publikation sind davon zu unterscheiden. Die bestehende Revisionsstufe kann die notwendigen Spezifikationen und figure_ids ergänzen, ohne die Aufgaben zu vereinfachen.

Diese Steuerungsregeln wurden nach dem erneuten Rohbefund MV-03 und der konkreten Abbildungslücke in A5 integriert. Ihre erfolgreiche frische End-to-End-Produktion ist wegen des dokumentierten Providerlimits noch nicht belegt.

### Abschließende ausführbare Verträge (NLP-Vorbereitung)

Finite kanonische Beispielmengen deklarieren `example_scope`: `selected` verlangt einen tatsächlich erreichbaren inneren Kontrollwert außerhalb der Referenzliste mit numerisch geprüftem Ergebnis; `exhaustive` muss jeden Sliderwert enthalten. Dies prüft strukturierte Angaben, keine automatische semantische TeX-/Prosaäquivalenz; Quellenbegutachtung bleibt Pflicht. Legacy-Objekte ohne diese Metadaten erhalten keinen Nachweis dieses neuen Teilvertrags.

Erforderliche Transfergrafiken werden als `visual_requirements` mit Zweck, exaktem Fallscope und konkreten IDs deklariert. Solutions darf diese Aufgabenanforderung nicht verändern; alle IDs müssen im Plan existieren und tatsächlich an die Lösung angehängt werden. Die fachliche Gleichheit von Fallscope und Grafikdaten bleibt separat zu auditieren.

Checkpoint-Eingangsidentitäten umfassen nun auch den vollständigen Enginehash. Frühere Rollenantworten werden bei Engineänderungen nicht ungeprüft wiederverwendet.

Ein ausdrücklich gemeldetes globales Provider-Nutzungslimit wird als USAGE_LIMIT protokolliert. Die Ein-Pfad-Produktion beendet danach die Einheitenschleife ohne weitere Modellversuche; alle verbleibenden Segmente bleiben sichtbar unverarbeitet und derselbe Startpfad dient zur Wiederaufnahme.

### Native APKG-Updates nach unabhängigen Exporten

Der Notiztyp selbst erhält wie Felder, Template und semantische Notiz-GUIDs eine stabile Identität. Neue Temporärsammlungen dürfen bei unveränderter Schema-Version keine neue Notiztyp-ID erzeugen. Das Standardverhalten des nativen Importers ohne automatische Typzusammenführung ist Pflicht; ein Backendtest mit aktivierter Zusammenführung beweist diesen Fall nicht. Getrennte Exporte werden mit geändertem Inhalt, festen Karten-/Notizidentitäten und erhaltenem Testverlauf geprüft. Die explizite Migration alter wechselnder Notiztyp-IDs bleibt ein eigener Vorgang; alte Pakete/Prüfprotokolle werden nicht rückwirkend verändert.

### Vollständiger Kursindex vor Materialproduktion

Die vorhandenen Visual-/Architect-Rollen planen zunächst sämtliche indizierten Transportpakete. Erst nach dieser Barriere beginnen die bestehenden übrigen Produktionsrollen. `course_competency_index.json` enthält prüfbare Blueprint-Verweise mit Hashes und nach Abschluss die gesamten Kompetenz-/Lerneinheitenbeiträge. Fehlende externe oder unlesbare Quellen bleiben als Vollständigkeitsgrenze sichtbar; ein Index aller verfügbaren Pakete ist keine unabhängige Fachfreigabe. Provider-/Vertragsfehler vor Abschluss stoppen die Planung, lassen keine vorgezogene Materialproduktion zu und bleiben mit exakt denselben Ein-Pfad-Checkpoints wiederaufnehmbar. Quellenbilder werden nur bei identischen Eingängen, vollständiger Referenzabdeckung und unveränderten Bildhashes wiederverwendet.
