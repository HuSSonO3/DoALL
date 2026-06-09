"""Tag definitions shared across recipe modules."""

RECIPE_TAG_GROUPS = {
    "Meal Type":  ["breakfast", "lunch", "dinner", "dessert", "snack", "side"],
    "Protein":    ["chicken", "beef", "pork", "seafood", "vegetarian", "vegan"],
    "Dish Type":  ["pasta", "soup", "salad", "bread", "rice", "stew"],
    "Cuisine":    ["italian", "mexican", "indian", "chinese", "japanese", "french", "american"],
    "Style":      ["quick", "slow-cooker", "baking", "grilled", "one-pot",
                   "spicy", "healthy", "comfort-food", "holiday"],
}

ALL_TAGS = [tag for tags in RECIPE_TAG_GROUPS.values() for tag in tags]
