# Nom du fichier UI Qt Designer (sans extension .ui)
UI_FILE = dorling_cartogram_dialog_base
UI_PY = $(UI_FILE).py
UI_SRC = $(UI_FILE).ui

# Fichier de ressources Qt (optionnel)
QRC_FILE = resources.qrc
QRC_PY = resources.py

# Commande principale
all: $(UI_PY) $(QRC_PY)

# Compilation du .ui → .py
$(UI_PY): $(UI_SRC)
	@echo "⏳ Compilation UI : $(UI_SRC) → $(UI_PY)"
	pyuic5 -o $@ $<

# Compilation du .qrc → .py (si présent)
$(QRC_PY): $(QRC_FILE)
	@echo "⏳ Compilation ressources : $(QRC_FILE) → $(QRC_PY)"
	pyrcc5 -o $@ $<

# Nettoyage des fichiers générés
clean:
	@echo "🧹 Suppression des fichiers générés"
	rm -f $(UI_PY) $(QRC_PY)