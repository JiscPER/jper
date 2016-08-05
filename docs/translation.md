**Übersetzung mit Flask Babel**

Die Installation von Babel sind Voraussetzung für die Ausführung des Programms. 

Zeitaufwand richtet sich danach wie viel übersetzt werden soll, geht es nur um die Hauptseiten so sollte dies innerhalb eines Tages zu schaffen sein, sollen alle Textbausteine die in Formularen etc. auftauchen übersetzt werden, wird es etwas länger dauern (ca. 2 bis 3 Tage für die Markierung, ca. 1 Tag für die Übersetzung). 

**1.**

Zunächst müssen alle Textstellen die übersetzt werden sollen für das Programm markiert werden. 

Bei .py Dateien setzt man die Strings dafür in gettext, also z.B. `(gettext("Missing required parameter"))`. 

Bei .html Dateien setzt man die Strings dafür in die verkürzte Variante {{ _() }} , also z.B. `{{ _('Publishers') }}` . Hier ist vor allem darauf zu achten dass keine html Befehle in der Klammer mit stehen, da diese nicht vom Programm erkannt werden und somit als zu übersetzenden Text markiert werden. Ein Text mit Link müsste also z.B. so markiert werden: `{{ _('Link to') }} <a href=“url“>{{ _('Publishers') }}</a>` .  

Es ist noch zu klären ob dies auch für strings innerhalb von flash Attributen gilt oder ob diese mit lazy_gettext markiert werden müssen, deren Auswertung erfolgt leicht anders, siehe das Tutorial. 

Ebenso muss überprüft werden ob die verkürzte Variante für html-Strings umsetzbar ist (also keine Probleme bei der live-Schaltung auftreten), oder ob auch hier die ausführliche Variante übernommen werden müsste. 

**2.**

Im Ordner 'Babel' befinden sich die notwendigen Dateien zum integrieren von Babel.

*__init__.py* : startet Babel und weist auf die Konfigurationsdatei hin. 

*views.py* :  legt fest welche Sprache benutzt werden soll. Im Moment wird überprüft welche Sprache der Browser des Nutzers bevorzugt, andere Einstellung sind aber möglich. So kann man in der config.py festlegen, welche Sprache die bevorzugte Sprache ist. 

*config.py* : legt fest welche Sprachen von Babel unterstützt werden sollen. Es kann noch eine bevorzugte Sprache (BABEL_DEFAULT_LOCALE = 'xx') und eine bevorzugte Zeitzone (BABEL_DEFAULT_TIMEZONE = 'xx') festgelegt werden. Für mehr Informationen zu diesen zwei Einstellungen siehe die offizielle Flask Babel Seite und das Tutorial. 

Die Konfigurationsdatei babel.cfg liegt im Root Verzeichnis. 

**3.**

Die Strings zu extrahieren und zu übersetzen erfolgt über cmd. Der Befehl hierzu sieht so aus:

`pybabel extract -F babel.cfg -o messages.pot service`

Aufbauend auf dieser .pot Datei wird nun ein Überestzungskatalog erstellt mit folgenden Befehl:

`pybabel init -i messages.pot -d service\translations -l de`

Der Aufbau des pybabel Befehls wird hier nochmal ausführlicher erklärt: http://babel.pocoo.org/en/latest/cmdline.html



**4.**

Zur Übersetzung der Textbausteine benötigt man einen Editor wie z.B. Poeditor (frei verfügbare Software). Ein Teil der Übersetzungen, hauptsächlich die .html Dateien zur Information über den Publications Router liegen bereits als Word Datei vor und müsse nur entsprechend eingefügt werden. 

Um die Übersetzung als .mo Datei zu veröffentlichen wird folgender Befehl benötigt:

`pybabel compile -d app/translations`


**5.**

Falls neue Textbausteine hinzukommen sollten, können diese über einen Aktualisierungsbefehl hinzugefügt werden. Dazu wiederholt man zunächst Schritt 1 und 3 und führt dann folgenden Befehl aus:

`pybabel update -i messages.pot -d service\translations`

Dann können diese Text übersetzt und anschließend veröffentlicht werden. 



Informationen übernommen von der offizielen Flask Babel Seite (https://pythonhosted.org/Flask-Babel/) und einem Tutorial (http://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-xiv-i18n-and-l10n) . 








