from personal_app.logic.shopping_manager import ShoppingManager


RECIPES = {
    "chicken tikka curry": ["chicken breast", "tikka paste", "onion", "garlic", "ginger", "tomatoes", "rice", "yoghurt"],
    "spaghetti bolognese": ["spaghetti", "beef mince", "onion", "garlic", "chopped tomatoes", "tomato puree", "parmesan"],
    "stir fry": ["noodles", "mixed vegetables", "soy sauce", "ginger", "garlic", "chicken or tofu"],
    "fajitas": ["tortillas", "chicken", "peppers", "onion", "fajita seasoning", "salsa", "sour cream"],
    "chilli con carne": ["beef mince", "kidney beans", "chopped tomatoes", "onion", "chilli powder", "rice"],
    "pesto pasta": ["pasta", "pesto", "parmesan", "cherry tomatoes", "spinach"],
    "teriyaki chicken": ["chicken thighs", "teriyaki sauce", "rice", "broccoli", "spring onions"],
    "breakfast oats": ["oats", "milk", "banana", "honey", "berries", "cinnamon"],
}


class RecipeManager:
    def __init__(self, shopping: ShoppingManager) -> None:
        self.shopping = shopping

    def recipe_names(self) -> list[str]:
        return sorted(RECIPES)

    def ingredients_for(self, name: str) -> list[str]:
        return RECIPES.get(name.strip().lower(), [])

    def add_to_grocery(self, ingredients: list[str]) -> None:
        for ingredient in ingredients:
            if ingredient.strip():
                self.shopping.add(ingredient.strip(), 1, "Recipe", "Grocery")
