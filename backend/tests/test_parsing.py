from app.services.parsing import (
    SplitOptions, detect_source, looks_like_ingredient, parse_ingredient,
    parse_ingredient_line, parse_recipe, split_steps,
)

README_EXAMPLE = """cut eggplant into strips, salt 10 min, pan fry till soft
fry garlic, ginger & doubanjiang, add pork"""


def test_readme_example_six_steps_with_comma_and_line():
    r = parse_recipe(README_EXAMPLE)
    assert [s["text"] for s in r.steps] == [
        "cut eggplant into strips", "salt 10 min", "pan fry till soft",
        "fry garlic", "ginger & doubanjiang", "add pork",
    ]
    assert r.ingredients == []


def test_readme_example_comma_off_gives_two_steps():
    r = parse_recipe(README_EXAMPLE, SplitOptions(comma=False))
    assert len(r.steps) == 2


def test_source_detection():
    assert detect_source("https://youtu.be/abc123") == "youtube"
    assert detect_source("https://www.youtube.com/watch?v=abc") == "youtube"
    assert detect_source("https://www.instagram.com/p/xyz/") == "instagram"
    assert detect_source("https://cooking.example.com/recipe/1") == "link"
    assert detect_source("2 eggs\n1 tomato") == "text"
    assert detect_source("look at https://youtu.be/abc") == "text"


def test_ingredient_patterns():
    i = parse_ingredient("2 cloves garlic")
    assert (i.name, i.amount, i.unit) == ("garlic", 2, "cloves")
    i = parse_ingredient("蒜頭 3瓣")
    assert (i.name, i.amount, i.unit) == ("蒜頭", 3, "瓣")
    i = parse_ingredient("1 1/2 cups flour")
    assert (i.name, i.amount, i.unit) == ("flour", 1.5, "cups")
    i = parse_ingredient("½ tsp salt")
    assert (i.name, i.amount, i.unit) == ("salt", 0.5, "tsp")
    i = parse_ingredient("兩顆蛋")
    assert (i.name, i.amount, i.unit) == ("蛋", 2, "顆")
    i = parse_ingredient("200g pork")
    assert (i.name, i.amount, i.unit) == ("pork", 200, "g")


def test_unit_needs_word_boundary():
    i = parse_ingredient("2 garlic")
    assert (i.name, i.amount, i.unit) == ("garlic", 2, None)
    i = parse_ingredient("1 large onion")
    assert (i.name, i.unit) == ("large onion", None)


def test_to_taste():
    assert parse_ingredient("鹽 適量").note == "適量"
    i = parse_ingredient("salt to taste")
    assert (i.name, i.amount, i.note) == ("salt", None, "to taste")


def test_chinese_numeral_needs_unit():
    assert parse_ingredient("二砂糖 1大匙").name == "二砂糖"


def test_ingredient_line_splits_on_commas():
    names = [i.name for i in parse_ingredient_line("2 eggs, 1 tomato、蔥 2根")]
    assert names == ["eggs", "tomato", "蔥"]


def test_prep_words_attach_to_previous():
    items = parse_ingredient_line("1 onion, chopped")
    assert len(items) == 1 and items[0].note == "chopped"


def test_heuristic_without_headers():
    assert looks_like_ingredient("2 eggs")
    assert looks_like_ingredient("蒜頭 3瓣")
    assert looks_like_ingredient("鹽 少許")
    assert looks_like_ingredient("pepper to taste")
    assert not looks_like_ingredient("1. Beat the eggs")
    assert not looks_like_ingredient("10 min later flip it")
    assert not looks_like_ingredient("Beat the eggs with a pinch of salt until frothy and pale")


def test_with_headers_and_intro_and_junk():
    text = """Our favourite weeknight dish!
Ingredients:
2 eggs
3 tomatoes
For the sauce:
1 tbsp soy sauce
作法：
1. Beat the eggs 2. Fry the tomatoes
3) Add eggs
#cooking #dinner https://example.com
0:00 intro"""
    r = parse_recipe(text)
    assert r.has_headers
    assert [i.name for i in r.ingredients] == ["eggs", "tomatoes", "soy sauce"]
    assert [s["text"] for s in r.steps] == ["Beat the eggs", "Fry the tomatoes", "Add eggs"]


def test_inline_header():
    r = parse_recipe("Ingredients: 2 eggs, 1 tomato\nSteps: fry it all")
    assert [i.name for i in r.ingredients] == ["eggs", "tomato"]
    assert [s["text"] for s in r.steps] == ["fry it all"]


def test_split_steps_options():
    text = "炒香蒜、薑。加入豬肉拌炒"
    assert [s["text"] for s in split_steps(text, SplitOptions(comma=False, period=True))] == ["炒香蒜、薑", "加入豬肉拌炒"]
    # pieces under 3 characters merge into the previous step
    assert [s["text"] for s in split_steps("爆香蒜、薑、蔥", SplitOptions(comma=True))] == ["爆香蒜薑蔥"]


def test_short_flag():
    steps = split_steps("Serve\nSimmer for twenty minutes")
    assert steps[0] == {"text": "Serve", "short": True}
    assert steps[1]["short"] is False


def test_bullets_trimmed():
    assert [s["text"] for s in split_steps("- chop onions\n• fry them")] == ["chop onions", "fry them"]


def _names(text):
    r = parse_recipe(text)
    return [i.name for i in r.ingredients], [s["text"] for s in r.steps]


def test_trailing_paren_note_is_kept_out_of_the_name():
    ings = parse_recipe("大蒜 3瓣（切末，拍碎）\n蔥 1根(切段)\n2 eggs (beaten)\n炒香").ingredients
    assert [(i.name, i.amount, i.unit, i.note) for i in ings] == [
        ("大蒜", 3, "瓣", "切末，拍碎"), ("蔥", 1, "根", "切段"), ("eggs", 2, None, "beaten"),
    ]


def test_name_then_bare_number():
    assert _names("Eggs 2\nTomatoes 3\nScramble the eggs") == (["Eggs", "Tomatoes"], ["Scramble the eggs"])


def test_multiplier():
    i = parse_ingredient("2x eggs")
    assert (i.name, i.amount) == ("eggs", 2)


def test_bare_items_next_to_ingredients():
    assert _names("1 lb chicken\nsalt & pepper\nolive oil\nSeason the chicken\nRoast 40 min") == (
        ["chicken", "salt & pepper", "olive oil"], ["Season the chicken", "Roast 40 min"],
    )
    assert _names("300g 豬絞肉\n蔥花\n薑末\n醬油 2大匙\n豬絞肉加調味料拌勻") == (
        ["豬絞肉", "蔥花", "薑末", "醬油"], ["豬絞肉加調味料拌勻"],
    )


def test_bare_list_without_quantities():
    assert _names("eggplant\ngarlic\nsoy sauce\nFry everything together until soft") == (
        ["eggplant", "garlic", "soy sauce"], ["Fry everything together until soft"],
    )
    assert _names("雞蛋、番茄、蔥\n番茄切塊，雞蛋打散\n先炒蛋再炒番茄")[0] == ["雞蛋", "番茄", "蔥"]


def test_short_steps_stay_steps():
    assert _names("Mix flour and water\nKnead\nRest 30 min\nRoll out")[0] == []
    assert _names("番茄切塊\n雞蛋打散\n先炒蛋再炒番茄")[0] == []
