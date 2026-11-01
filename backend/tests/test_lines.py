import pytest

from app.services.lines import parse_line, parse_lines, parse_portion

CASES = [
    # line, name, portion, amount, unit
    ("雞腿 300g", "雞腿", "300g", 300, "g"),
    ("大蒜 1瓣", "大蒜", "1瓣", 1, "瓣"),
    ("雞腿300g", "雞腿", "300g", 300, "g"),
    ("雞蛋 3 顆", "雞蛋", "3 顆", 3, "顆"),
    ("大蒜 兩瓣", "大蒜", "兩瓣", 2, "瓣"),
    ("米酒 1/2杯", "米酒", "1/2杯", 0.5, "杯"),
    ("豬五花 1斤", "豬五花", "1斤", 1, "斤"),
    ("二砂糖 1大匙", "二砂糖", "1大匙", 1, "大匙"),
    ("大蒜 1瓣（拍碎）", "大蒜", "1瓣（拍碎）", 1, "瓣"),
    ("番茄 2 顆，切塊", "番茄", "2 顆，切塊", 2, "顆"),
    ("牛奶 約200ml", "牛奶", "約200ml", 200, "ml"),
    ("鹽 少許", "鹽", "少許", None, None),
    ("香菜", "香菜", None, None, None),
    ("五香粉", "五香粉", None, None, None),
    ("300g 雞腿", "雞腿", "300g", 300, "g"),
    ("兩顆蛋", "蛋", "兩顆", 2, "顆"),
    ("Chicken thigh 300 g", "Chicken thigh", "300 g", 300, "g"),
    ("Eggs 2", "Eggs", "2", 2, None),
    ("Olive oil: 2 tbsp", "Olive oil", "2 tbsp", 2, "tbsp"),
    ("olive oil, 2 tbsp", "olive oil", "2 tbsp", 2, "tbsp"),
    ("2 cloves garlic", "garlic", "2 cloves", 2, "cloves"),
    ("1 cup of rice", "rice", "1 cup", 1, "cup"),
    ("2x eggs", "eggs", "2", 2, None),
    ("Salt to taste", "Salt", "to taste", None, None),
    ("5-spice powder 1 tsp", "5-spice powder", "1 tsp", 1, "tsp"),
    ("- 200 ml milk", "milk", "200 ml", 200, "ml"),
    ("1. 雞腿 300g", "雞腿", "300g", 300, "g"),
]


@pytest.mark.parametrize("line,name,portion,amount,unit", CASES)
def test_parse_line(line, name, portion, amount, unit):
    ing = parse_line(line)
    assert (ing.name, ing.portion, ing.amount, ing.unit) == (name, portion, amount, unit)


def test_compound_portion_adds_up_in_base_units():
    ing = parse_line("醬油 1大匙 + 1小匙")
    assert (ing.name, ing.portion, ing.amount, ing.unit) == ("醬油", "1大匙 + 1小匙", 4, "tsp")


def test_one_ingredient_per_line_nothing_split_or_dropped():
    ings = parse_lines("雞腿 300g\n\n大蒜 1瓣\n雞蛋、番茄\n")
    assert [i.name for i in ings] == ["雞腿", "大蒜", "雞蛋、番茄"]


def test_portion_field_is_never_rejected():
    assert parse_portion("a handful")["note"] == "a handful"
    assert parse_portion("")["portion"] is None
    p = parse_portion("2根(切段)")
    assert (p["amount"], p["unit"], p["note"]) == (2, "根", "切段")
