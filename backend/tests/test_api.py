def _recipe(client, name, ingredients, steps=("cook",)):
    r = client.post("/api/recipes", json={
        "name": name,
        "source": "manual",
        "ingredients": [{"name": n, "amount": a, "qty": str(a) if a else None, "unit": u} for n, a, u in ingredients],
        "steps": list(steps),
    })
    assert r.status_code == 201, r.text
    return r.json()


def test_auth_required(db):
    from fastapi.testclient import TestClient

    from app.main import app

    c = TestClient(app)
    assert c.get("/api/recipes").status_code == 401
    assert c.post("/api/auth/login", json={"member": "Mei", "passcode": "nope"}).status_code == 401
    assert c.post("/api/auth/login", json={"member": "Eve", "passcode": "1234"}).status_code == 401
    assert c.get("/api/auth/household").json()["members"][1] == {"name": "Paul", "name_zh": "Paul"}


def test_recipe_lifecycle_and_search(client):
    shak = _recipe(client, "Shakshuka", [("eggs", 4, None), ("tomatoes", 3, None), ("cumin", 1, "tsp")])
    yu = _recipe(client, "魚香茄子", [("茄子", 2, "條"), ("豬絞肉", 150, "g"), ("蔥", 2, "根")])
    udon = _recipe(client, "Curry Udon", [("udon", 2, "packs"), ("scallion", 1, "bunch"), ("egg", 1, None)])

    assert shak["made_count"] == 0 and shak["name"] == "Shakshuka"

    # log a cook, pick a plate
    r = client.post(f"/api/recipes/{udon['id']}/logs", json={"rating": 4, "note": "good"})
    assert r.status_code == 201
    r = client.patch(f"/api/recipes/{udon['id']}", json={"plate_id": "celadon"})
    assert r.json()["plate_id"] == "celadon" and r.json()["made_count"] == 1 and r.json()["avg_rating"] == 4

    # cross-language alias: "蔥" finds Scallion, made recipes first
    res = client.get("/api/search", params={"q": "蔥"}).json()
    assert [x["name"] for x in res["results"]] == ["Curry Udon", "魚香茄子"]
    assert res["results"][0]["matched_index"] == 1

    # "egg" must not match eggplant via contains
    res = client.get("/api/search", params={"q": "egg"}).json()
    assert {x["name"] for x in res["results"]} == {"Shakshuka", "Curry Udon"}
    res = client.get("/api/search", params={"q": "eggplant"}).json()
    assert [x["name"] for x in res["results"]] == ["魚香茄子"]
    # prefix fallback while typing
    assert client.get("/api/search", params={"q": "tom"}).json()["count"] == 1

    lst = client.get("/api/recipes", params={"filter": "not_made"}).json()
    assert lst["counts"] == {"all": 3, "made": 1, "not_made": 2}
    assert {x["name"] for x in lst["recipes"]} == {"Shakshuka", "魚香茄子"}
    # recipes tab matches names too
    assert client.get("/api/recipes", params={"q": "udon"}).json()["recipes"][0]["name"] == "Curry Udon"


def test_grocery_flow(client):
    shak = _recipe(client, "Shakshuka", [("eggs", 2, None), ("onion", 1, None)])
    udon = _recipe(client, "Curry Udon", [("egg", 1, None), ("udon", 2, "packs")])

    client.post("/api/grocery/from-recipe", json={"recipe_id": shak["id"], "indices": [0]})
    g = client.post("/api/grocery/from-recipe", json={"recipe_id": udon["id"], "indices": [0, 1]}).json()
    assert g["added"] == 2 and g["open_count"] == 2
    eggs = next(i for i in g["open"] if i["key"] == "egg")
    assert eggs["qty"] == "3"
    assert [s["from"] for s in eggs["sources"]] == ["Shakshuka", "Curry Udon"]

    g = client.post("/api/grocery", json={"text": "2 onions"}).json()
    onion = next(i for i in g["open"] if i["key"] == "onion")
    assert onion["qty"] == "2" and onion["sources"][0]["by"] == "Mei" and onion["sources"][0]["from"] is None

    g = client.patch(f"/api/grocery/{onion['id']}", json={"checked": True}).json()
    assert g["open_count"] == 2 and len(g["basket"]) == 1
    g = client.post("/api/grocery/clear").json()
    assert g["basket"] == []


def test_parse_endpoint(client):
    r = client.post("/api/parse", json={"input": "2 eggs\n1 tomato\nBeat eggs, fry tomato"}).json()
    assert r["source"] == "text" and r["status"] == "ok"
    assert len(r["ingredients"]) == 2 and len(r["steps"]) == 2

    r = client.post("/api/parse", json={"input": "https://www.instagram.com/p/abc/"}).json()
    assert r["status"] == "needs_caption"
    r = client.post("/api/parse", json={"input": "https://www.instagram.com/p/abc/", "caption": "Ingredients: 2 eggs"}).json()
    assert r["status"] == "ok" and r["ingredients"][0]["name"] == "eggs"

    r = client.post("/api/parse", json={"input": "https://youtu.be/abc"}).json()
    assert r["status"] == "fetch_failed"  # no API key in tests
    r = client.post("/api/parse", json={"input": "example.com/recipe"}).json()
    assert r["status"] == "link_only" and r["url"] == "https://example.com/recipe"


def test_photos_and_logs(client):
    rec = _recipe(client, "Toast", [("bread", 2, "slices")])
    up = client.post("/api/photos", files={"file": ("a.jpg", b"\xff\xd8\xff fake", "image/jpeg")})
    assert up.status_code == 201
    log = client.post(f"/api/recipes/{rec['id']}/logs", json={"photo_id": up.json()["id"], "rating": 5}).json()
    assert log["photo_url"] == up.json()["url"]
    assert client.get(up.json()["url"]).content.startswith(b"\xff\xd8")
    detail = client.get(f"/api/recipes/{rec['id']}").json()
    assert detail["photo_url"] == up.json()["url"] and len(detail["logs"]) == 1
    assert client.delete(f"/api/logs/{log['id']}").status_code == 204
    assert client.get(f"/api/recipes/{rec['id']}").json()["made_count"] == 0
    assert client.post("/api/photos", files={"file": ("a.txt", b"x", "text/plain")}).status_code == 415


def test_empty_passcode_never_logs_in(db, monkeypatch):
    from fastapi.testclient import TestClient

    from app.config import get_settings
    from app.main import app

    monkeypatch.setattr(get_settings(), "mela_passcode", "")
    c = TestClient(app)
    assert c.post("/api/auth/login", json={"member": "Mei", "passcode": ""}).status_code == 401


def test_structured_ingredients_keep_portion_as_typed(client):
    r = client.post("/api/parse/lines", json={"text": "雞腿 300g\n大蒜 1瓣\n鹽 少許"}).json()
    assert [(i["name"], i["portion"]) for i in r["ingredients"]] == [("雞腿", "300g"), ("大蒜", "1瓣"), ("鹽", "少許")]

    rec = client.post("/api/recipes", json={
        "name": "三杯雞",
        "ingredients": [{"name": "雞腿", "portion": "300g"}, {"name": "大蒜", "portion": "1瓣（拍碎）"}, {"name": "九層塔"}],
        "steps": ["雞腿切塊", "爆香大蒜"],
    }).json()
    ings = rec["ingredients"]
    assert [(i["name"], i["portion"], i["amount"], i["unit"]) for i in ings] == [
        ("雞腿", "300g", 300, "g"), ("大蒜", "1瓣（拍碎）", 1, "瓣"), ("九層塔", None, None, None),
    ]
    g = client.post("/api/grocery/from-recipe", json={"recipe_id": rec["id"], "indices": [0]}).json()
    assert g["open"][0]["qty"] == "300" and g["open"][0]["unit"] == "g"
    g = client.post("/api/grocery", json={"text": "雞腿 200g"}).json()
    assert len(g["open"]) == 1 and g["open"][0]["qty"] == "500"
