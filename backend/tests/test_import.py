import io
import json
import zipfile
from pathlib import Path

from app.services.importer import ingredient_from_text, parse_markdown, parse_upload

EXAMPLE = Path(__file__).resolve().parents[2] / "web" / "public" / "mela-import-example.md"


def test_example_file():
    r = parse_markdown(EXAMPLE.read_text(encoding="utf-8"))
    assert [x.name for x in r.recipes] == ["三杯雞", "Shakshuka", "Curry udon"]

    sanbei, shak, udon = r.recipes
    assert sanbei.source == "youtube" and sanbei.source_url.endswith("abc123")
    assert sanbei.name_alt == "Three-cup chicken" and sanbei.note == "媽媽的做法，九層塔要最後放"
    assert [(i["name"], i["portion"]) for i in sanbei.ingredients][:4] == [
        ("雞腿", "600g"), ("大蒜", "10瓣"), ("薑", "1塊"), ("九層塔", "一把"),
    ]
    assert sanbei.ingredients[0]["amount"] == 600 and sanbei.ingredients[0]["unit"] == "g"
    assert sanbei.steps[3] == "加醬油、米酒、冰糖，蓋鍋燜 15 分鐘"
    (a, b) = sanbei.logs
    assert (str(a.cooked_on), a.rating, a.created_by, a.note) == ("2026-10-24", 5, "Mei", "收汁收得剛好")
    assert (b.rating, b.note, b.tweaks) == (4, "太甜了", "冰糖減半")

    assert shak.name_alt == "番茄燉蛋"
    assert [(i["name"], i["portion"]) for i in shak.ingredients][-2:] == [("Feta", "to taste"), ("Olive oil", "2 tbsp")]
    assert len(shak.steps) == 4 and shak.logs == []

    assert udon.source == "instagram" and udon.ingredients == [] and udon.note == "Not cooked yet, just saving the link."
    assert not sanbei.warnings and not shak.warnings


def test_separator_beats_guessing():
    assert ingredient_from_text("- 7up — 1 can")["name"] == "7up"
    ing = ingredient_from_text("- 蛋黃 | 2")
    assert (ing["name"], ing["portion"]) == ("蛋黃", "2")
    assert ingredient_from_text("- 香菜")["portion"] is None


def test_headings_variants_and_warnings():
    # only "# " headings: each is a recipe
    r = parse_markdown("# 媽媽的菜\n\n前言\n# 滷肉\n五花肉 600g\n")
    assert [x.name for x in r.recipes] == ["媽媽的菜", "滷肉"]

    r = parse_markdown("## 滷肉\n### 材料\n五花肉 600g\n### 作法\n1. 切丁\n   再炒香\n2. 加醬油\n### 小撇步\n多燉一點\n### 紀錄\n上週做的\n")
    (x,) = r.recipes
    assert x.steps == ["切丁 再炒香", "加醬油"]
    assert any("小撇步" in w for w in x.warnings) and any("without a date" in w for w in x.warnings)


def test_no_headings_is_one_recipe_named_after_the_file():
    r = parse_upload("番茄炒蛋.txt", "雞蛋 3顆\n番茄 2顆\n".encode())
    assert r.recipes[0].name == "番茄炒蛋"


def test_big5_text():
    r = parse_upload("old.txt", "## 滷肉飯\n### 材料\n- 五花肉 — 600g\n".encode("big5"))
    assert r.recipes[0].ingredients[0]["name"] == "五花肉"


def test_json_list():
    data = [{"title": "Toast", "ingredients": ["2 slices bread", {"name": "butter", "portion": "1 tbsp"}],
             "instructions": "1. Toast\n2. Butter", "logs": [{"date": "2026/01/02", "rating": 4, "by": "Paul"}]}]
    r = parse_upload("x.json", json.dumps(data).encode())
    (t,) = r.recipes
    assert [(i["name"], i["portion"]) for i in t.ingredients] == [("bread", "2 slices"), ("butter", "1 tbsp")]
    assert t.steps == ["Toast", "Butter"] and t.logs[0].rating == 4 and t.logs[0].created_by == "Paul"


def _zip(files: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for name, data in files.items():
            zf.writestr(name, data)
    return buf.getvalue()


def test_zip_of_text_files():
    r = parse_upload("old.zip", _zip({"a.md": "## A\n### Steps\n- x\n", "sub/b.txt": "## B\n### Steps\n- y\n", "pic.jpg": b"x"}))
    assert sorted(x.name for x in r.recipes) == ["A", "B"]


def test_round_trip_through_export(client):
    r = client.post("/api/import", files={"file": ("ex.md", EXAMPLE.read_bytes(), "text/markdown")}, data={"dry_run": "false"}).json()
    assert r["imported"] == 3 and r["counts"] == {"found": 3, "new": 3, "duplicates": 0}
    rec = client.get("/api/recipes", params={"q": "三杯雞"}).json()["recipes"][0]
    assert rec["made_count"] == 2 and rec["avg_rating"] == 4.5
    up = client.post("/api/photos", files={"file": ("a.jpg", b"\xff\xd8\xff photo", "image/jpeg")}).json()
    client.post(f"/api/recipes/{rec['id']}/logs", json={"photo_id": up["id"], "photo_crop": {"cx": 0.4, "cy": 0.5, "zoom": 1.5, "aspect": 1.5}})
    client.patch(f"/api/recipes/{rec['id']}", json={"plate_id": "garland"})

    backup = client.get("/api/export").content

    # importing into the same kitchen: all duplicates, nothing saved
    r = client.post("/api/import", files={"file": ("b.zip", backup, "application/zip")}, data={"dry_run": "false"}).json()
    assert r["kind"] == "backup" and r["imported"] == 0 and r["counts"]["duplicates"] == 3

    # restore into an empty kitchen
    for x in client.get("/api/recipes").json()["recipes"]:
        client.delete(f"/api/recipes/{x['id']}")
    preview = client.post("/api/import", files={"file": ("b.zip", backup, "application/zip")}).json()
    assert preview["dry_run"] and preview["imported"] == 0 and preview["total_recipes"] == 0
    assert next(x for x in preview["recipes"] if x["name"] == "三杯雞")["photos"] == 1
    r = client.post("/api/import", files={"file": ("b.zip", backup, "application/zip")}, data={"dry_run": "false"}).json()
    assert r["imported"] == 3 and r["total_recipes"] == 3

    back = client.get(f"/api/recipes/{rec['id']}").json()  # same id as before
    assert back["plate_id"] == "garland" and back["made_count"] == 3
    assert back["photo_crop"]["zoom"] == 1.5 and client.get(back["photo_url"]).content == b"\xff\xd8\xff photo"
    assert [(i["name"], i["portion"]) for i in back["ingredients"]][:2] == [("雞腿", "600g"), ("大蒜", "10瓣")]

    # the readable recipes.md from the export imports too (same names -> duplicates)
    md = zipfile.ZipFile(io.BytesIO(backup)).read("recipes.md")
    r = client.post("/api/import", files={"file": ("recipes.md", md, "text/markdown")}).json()
    assert r["counts"] == {"found": 3, "new": 0, "duplicates": 3}
    r = client.post("/api/import", files={"file": ("recipes.md", md, "text/markdown")},
                    data={"dry_run": "false", "skip_duplicates": "false"}).json()
    assert r["imported"] == 3 and r["total_recipes"] == 6
    again = [x for x in client.get("/api/recipes", params={"q": "三杯雞"}).json()["recipes"]]
    assert len(again) == 2 and all(x["made_count"] == 3 for x in again)


def test_bad_files(client):
    assert client.post("/api/import", files={"file": ("x.pdf", b"%PDF", "application/pdf")}).status_code == 422
    r = client.post("/api/import", files={"file": ("x.json", b"{oops", "application/json")})
    assert r.status_code == 422 and "isn't valid" in r.json()["detail"]
    assert client.post("/api/import", files={"file": ("x.zip", b"PK\x03\x04broken", "application/zip")}).status_code == 422


def test_utf16_with_bom():
    r = parse_upload("note.txt", "## 滷肉飯\n### 材料\n- 五花肉 — 600g\n".encode("utf-16"))
    assert r.recipes[0].ingredients[0]["portion"] == "600g"
