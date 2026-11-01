from app.services.grocery import add_to_grocery, item_out


def test_merges_same_key_and_unit(db):
    a = add_to_grocery(db, name="eggs", amount=2, unit=None, by="Mei", source="Shakshuka")
    b = add_to_grocery(db, name="Egg", amount=1, unit=None, by="Mei", source="Curry Udon")
    assert a.id == b.id
    out = item_out(b)
    assert out["qty"] == "3" and out["unitless"]
    assert [(s["from"], s["amount"]) for s in out["sources"]] == [("Shakshuka", 2), ("Curry Udon", 1)]


def test_converts_units(db):
    add_to_grocery(db, name="pork", amount=600, unit="g", by="Mei", source="A")
    item = add_to_grocery(db, name="豬肉", amount=0.4, unit="kg", by="Paul", source="B")
    assert item_out(item)["qty"] == "1" and item_out(item)["unit"] == "kg"


def test_tbsp_display(db):
    add_to_grocery(db, name="soy sauce", amount=1, unit="tbsp", by="Mei")
    item = add_to_grocery(db, name="醬油", amount=3, unit="小匙", by="Mei")
    assert (item_out(item)["qty"], item_out(item)["unit"]) == ("2", "tbsp")


def test_incompatible_units_stay_separate(db):
    a = add_to_grocery(db, name="scallion", amount=1, unit="bunch", by="Mei")
    b = add_to_grocery(db, name="green onion", amount=2, unit="stalks", by="Mei")
    assert a.id != b.id and a.key == b.key


def test_checked_items_never_merge(db):
    a = add_to_grocery(db, name="onion", amount=1, unit=None, by="Mei")
    a.checked = True
    db.flush()
    b = add_to_grocery(db, name="onions", amount=2, unit=None, by="Paul")
    assert a.id != b.id
