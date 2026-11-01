from app.services.normalize import base_unit, display_amount, key_for


def test_aliases_cross_languages():
    assert key_for("Scallion") == key_for("green onion") == key_for("青蔥") == key_for("蔥") == "scallion"
    assert key_for("aubergine") == key_for("茄子") == "eggplant"


def test_depluralise():
    assert key_for("eggs") == "egg"
    assert key_for("Tomatoes") == "tomato"
    assert key_for("berries") == "berry"
    assert key_for("glass") == "glass"


def test_units():
    assert base_unit("kg") == ("g", 1000)
    assert base_unit("克") == ("g", 1)
    assert base_unit("tbsp") == ("tsp", 3)
    assert base_unit("大匙") == ("tsp", 3)
    assert base_unit("l") == ("ml", 1000)
    assert base_unit("cloves") == ("clove", 1)
    assert base_unit(None) == (None, 1)


def test_display():
    assert display_amount(1000, "g") == ("1", "kg")
    assert display_amount(1500, "g") == ("1.5", "kg")
    assert display_amount(6, "tsp") == ("2", "tbsp")
    assert display_amount(4, "tsp") == ("4", "tsp")
    assert display_amount(2.5, None) == ("2.5", None)
    assert display_amount(None, None) == (None, None)
