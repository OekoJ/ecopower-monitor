# Ökostrom-Tagesverlaufs-Monitor

In dem Projekt [Ökostrom-Anzeige](https://ecomakerspace.de/oekostrom/) dessen Code unter https://github.com/OekoJ/ecopower zu finden ist, habe ich bereits ein analoges Anzeigegerät vorgestellt, das jeweils den aktuellen Anteil an Ökostrom im deutschen Stromnetz anzeigt. Der Anzeiger dient dazu, den Fortschritt der Energiewende sichtbar zu machen und nach Möglichkeit seinen eigenen Stromverbrauch am aktuellen Ökostrom-Anteil auszurichten. Das Projekt um das es jetzt gehen soll, ist ein bisschen technischer und richtet sich an Leute, die gerne Kurvendiagramme lesen. Mit dem hier vorgestellten Ökostrom-Tagesverlaufs-Monitor wird der bereits erzeugte und für die nächsten Stunden erwartete Anteil an Ökostrom im Stromnetz als Kurve dargestellt. Ein Zeiger zeigt auf die aktuellen Werte. Die Werte stammen vom Fraunhofer Institut für Solare Energiesysteme (ISE) und werden zirka stündlich aktualisiert.

Um das Projekt zu realisieren, habe ich auf ein zweifarbiges eInk-Display zurück gegriffen, das noch in meiner Schublade lag. Es ist das [Inky pHat Display](http://pimoroni.com/inkyphat) von Pimoroni, für das ich schon länger eine sinnvolle Anwendung gesucht habe. Der Code ist für das Display mit einer Auflösung von 212 x 104 geschrieben und muss angepasst werden, wenn man ein (neueres) Display mit einer höheren Auflösung verwendet. Das eInk-Display ist an einen Raspberry Pi Zero WH angeschlossen.

So sieht die Anzeige im Zeitraffer über den Zeitraum einer Woche aus:

| ![animated gif](ecopower-screenshots-animated.gif "Ökostrom-Monitor") |
|-|

Die x-Achse ist der Tagesverlauf von 0 Uhr bis 24 Uhr. Die y-Achse ist bei 12 Uhr eingezeichnet und zeigt den Ökostrom-Anteil von 0 bis 100%. Die untere Kurve (helle Fläche) stellt den Anteil an Ökostrom aus Biomasse dar. Die mittlere Kurve (etwas dunkler) zeigt den Strom aus Windkraftanlagen an. Und die rote Fläche (oben) den Solarstrom aus Photovoltaik-Anlagen, der sein Maximum am frühen Nachmittag erreicht, wenn die Sonne am stärksten scheint.

## Installation

Zunächst muss die python-Library des Displays installiert werden (https://github.com/pimoroni/inky).

Dann wird der Skript-Ordner `ecopower/` ins Verzeicnis `/home/pi/` kopiert (oder an eine andere Stelle).

Das Skript wird dann einfach mit `python3 ~/ecopower/ecopower.py` ohne Parameter aufgerufen.

Um die Anzeige alle 5 Minuten zu aktualisieren, habe ich mit `crontab -e` einen Cronjob eingerichtet:

`*/5 * * * *  python3 ~/ecopower/ecopower.py >> ~/ecopower/output.log 2>&1`

Die Consolen-Ausgabe wird in die Datei `~/ecopower/output.log` umgelenkt, damit man beobachten kann, ob das Skript funktioniert, oder ob es Fehler auswirft. 

Und um zu erreichen, dass die Anzeige gleich nach dem Einschalten des Raspberry Pis aktualisiert wird, habe ich zusätzlich eine Zeile in die Cron-Tabelle geschrieben, die das Skript nach dem Booten und einer kurzen Verzögerung von 20 Sekunden (bis das WLAN verbunden ist) startet:

`@reboot  /usr/bin/sleep 20; python3 ~/ecopower/ecopower.py >> ~/ecopower/output.log 2>&1`
