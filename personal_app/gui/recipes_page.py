from PySide6.QtWidgets import QComboBox, QLabel, QPushButton, QTextEdit

from personal_app.app import AppContext
from personal_app.gui.widgets import Compartment


class RecipesPage(Compartment):
    def __init__(self, context: AppContext) -> None:
        super().__init__("Recipes", "Generate ingredient lists and send them straight to grocery shopping.", "Recipes")
        self.context = context
        self.recipe = QComboBox()
        self.recipe.setEditable(True)
        self.recipe.addItems(context.recipes.recipe_names())
        self.recipe.currentTextChanged.connect(self.fill)
        self.ingredients = QTextEdit()
        self.ingredients.setPlaceholderText("One ingredient per line")
        add = QPushButton("Add ingredients to grocery")
        add.clicked.connect(self.add_to_grocery)
        self.notice = QLabel()
        self.layout.addWidget(self.recipe)
        self.layout.addWidget(self.ingredients, 1)
        self.layout.addWidget(add)
        self.layout.addWidget(self.notice)
        self.fill(self.recipe.currentText())

    def fill(self, name: str) -> None:
        ingredients = self.context.recipes.ingredients_for(name)
        if ingredients:
            self.ingredients.setPlainText("\n".join(ingredients))

    def add_to_grocery(self) -> None:
        ingredients = [line.strip() for line in self.ingredients.toPlainText().splitlines() if line.strip()]
        self.context.recipes.add_to_grocery(ingredients)
        self.notice.setText(f"Added {len(ingredients)} ingredient(s) to grocery.")
