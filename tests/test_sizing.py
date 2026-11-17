from dailymessage.sizing import BASE_H, BASE_W, estimate_size


def test_empty_and_growth():
    assert estimate_size([]) == (BASE_W, BASE_H)
    short = estimate_size([{"type": "text", "style": "body", "text": "Oi"}])
    long = estimate_size([{"type": "text", "style": "body", "text": "palavra " * 800}])
    assert long[1] > short[1] > BASE_H


def test_image_widens_and_checklist_grows():
    w, h = estimate_size([{"type": "image", "file": "0" * 32 + ".png", "caption": ""}])
    assert w > BASE_W and h > BASE_H
    _, h2 = estimate_size([{"type": "checklist", "title": "", "items": ["a", "b", "c"], "required": True}])
    assert h2 > BASE_H


def test_larger_font_increases_estimated_height():
    blocks = [{"type": "text", "style": "body", "text": "Uma mensagem longa " * 100}]
    assert estimate_size(blocks, 28)[1] > estimate_size(blocks, 16)[1]


def test_retype_blocks_expand_height_and_width():
    rules = {"type": "retype_rules", "title": "Regras", "items": ["regra 1", "regra 2", "regra 3"]}
    text = {"type": "retype_text", "title": "Compromisso", "text": "Eu assumo.\nEu confirmo."}
    rules_size = estimate_size([rules])
    text_size = estimate_size([text])
    assert rules_size[0] > BASE_W and rules_size[1] > BASE_H + 200
    assert text_size[0] > BASE_W and text_size[1] > BASE_H + 300
    assert estimate_size([rules, text])[1] > max(rules_size[1], text_size[1])
