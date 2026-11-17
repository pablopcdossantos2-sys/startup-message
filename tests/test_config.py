import json

from dailymessage import config
from dailymessage.config import MAX_BLOCKS, MAX_SECONDS, MAX_TEXT_LEN, MAX_TOTAL_TEXT, MIN_SECONDS, Config

HEX = "0" * 32


def test_parse_seconds():
    assert config.parse_seconds("10") == 10
    assert config.parse_seconds(" 15 ") == 15
    assert config.parse_seconds(str(MIN_SECONDS - 1)) is None
    assert config.parse_seconds(str(MAX_SECONDS + 1)) is None
    assert config.parse_seconds("abc") is None
    assert config.parse_seconds("") is None
    assert config.parse_seconds("-5") is None


def test_sanitized_clamps_and_defaults():
    cfg = Config(seconds=9999, theme="neon", accent="x", language="fr", blocks="lixo").sanitized()
    assert cfg.seconds == MAX_SECONDS
    assert cfg.theme == "system" and cfg.accent == "indigo" and cfg.language == "auto"
    assert cfg.blocks  # tipo inválido volta ao padrão
    assert cfg.font_family == config.DEFAULT_FONT_FAMILY
    assert cfg.font_size == config.DEFAULT_FONT_SIZE
    assert Config(font_size=99).sanitized().font_size == config.MAX_FONT_SIZE
    assert Config(font_family="  " + "A" * 200).sanitized().font_family == "A" * 80
    assert not config.IMAGE_NAME_RE.fullmatch(HEX + ".png\\n")
    assert Config(seconds=True).sanitized().seconds == config.DEFAULT_SECONDS


def test_blocks_sanitize():
    raw = [
        {"type": "text", "text": "  oi  ", "style": "x"},
        {"type": "text", "text": "   "},
        {"type": "image", "file": "../../etc/passwd"},
        {"type": "image", "file": HEX + ".png", "caption": " legenda "},
        {"type": "checklist", "items": ["a", " ", 5, "b"]},
        {"type": "checklist", "items": []},
        "lixo",
        {"type": "zzz"},
    ]
    out = config.sanitize_blocks(raw)
    assert [b["type"] for b in out] == ["text", "image", "checklist"]
    assert out[0] == {"type": "text", "style": "body", "text": "oi"}
    assert out[1]["caption"] == "legenda"
    assert out[2]["items"] == ["a", "b"] and out[2]["required"] is True


def test_block_limits():
    many = [{"type": "text", "text": "x"}] * 100
    assert len(config.sanitize_blocks(many)) == MAX_BLOCKS
    big = [{"type": "text", "text": "x" * MAX_TEXT_LEN}] * 3
    out = config.sanitize_blocks(big)
    assert sum(len(b["text"]) for b in out) <= MAX_TOTAL_TEXT
    assert config.text_too_long(big)


def test_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "config_dir", lambda: tmp_path)
    blocks = [
        {"type": "text", "style": "heading", "text": "Olá"},
        {"type": "checklist", "title": "Antes de começar", "items": ["Café", "Agenda"], "required": True},
    ]
    original = Config(title="Oi", blocks=blocks, seconds=20, theme="dark", font_family="Georgia", font_size=22)
    config.save(original)
    assert config.load() == original


def test_load_handles_winrt_unavailable(monkeypatch):
    def missing_winrt():
        raise ImportError("winrt indisponível")
    monkeypatch.setattr(config, "config_path", missing_winrt)
    assert config.load() == Config()


def test_first_run_english_uses_localized_defaults(tmp_path, monkeypatch):
    from dailymessage import i18n
    monkeypatch.setattr(config, "config_dir", lambda: tmp_path)
    monkeypatch.setattr(i18n, "detect_system_language", lambda: "en")
    cfg = config.load()
    assert cfg.title == "Welcome!"
    assert "productive day" in cfg.blocks[0]["text"]


def test_existing_content_remains_unchanged_on_english_windows(tmp_path, monkeypatch):
    from dailymessage import i18n
    monkeypatch.setattr(config, "config_dir", lambda: tmp_path)
    monkeypatch.setattr(i18n, "detect_system_language", lambda: "en")
    saved = config.Config(title="Meu texto", blocks=[{"type": "text", "style": "body", "text": "Olá"}])
    config.save(saved)
    assert config.load() == saved


def test_load_corrupted_returns_defaults(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "config_dir", lambda: tmp_path)
    (tmp_path / "config.json").write_text("{ not json", encoding="utf-8")
    assert config.load() == Config()


def test_migrates_old_message_field(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "config_dir", lambda: tmp_path)
    (tmp_path / "config.json").write_text(json.dumps({"message": "Olá", "seconds": 5}), encoding="utf-8")
    cfg = config.load()
    assert cfg.blocks[0]["text"] == "Olá" and cfg.seconds == 5


def test_retype_blocks_roundtrip_and_legacy_backwards_compatibility(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "config_dir", lambda: tmp_path)
    rules = config.new_block("retype_rules")
    rules.update(title="Regras diárias", items=["Respeitar meus limites", "Planejar antes de executar"])
    long_text = config.new_block("retype_text")
    long_text.update(title="Compromisso", text="Prometo agir com disciplina.\nNão improvisar.")
    previous = {"type": "checklist", "title": "Rotina", "items": ["Beber água"], "required": True}
    cfg = Config(blocks=[previous, rules, long_text])
    config.save(cfg)
    loaded = config.load()
    assert loaded.blocks == cfg.blocks
    assert len(loaded.blocks) == 3


def test_invalid_retype_blocks_are_dropped():
    assert config.sanitize_blocks([
        {"type": "retype_rules", "items": []},
        {"type": "retype_rules", "items": "not-a-list"},
        {"type": "retype_text", "text": "  "},
        {"type": "retype_rules", "title": "  Regras  ", "items": [" regra  ", "", 10]},
        {"type": "retype_text", "title": "  Texto  ", "text": " linha 1\nlinha 2  "},
    ]) == [
        {"type": "retype_rules", "title": "Regras", "items": ["regra"]},
        {"type": "retype_text", "title": "Texto", "text": "linha 1\nlinha 2"},
    ]


def test_limits_cover_all_required_transcriptions():
    assert config.text_too_long([{"type": "retype_text", "text": "x" * (MAX_TEXT_LEN + 1)}])
    assert config.text_too_long([
        {"type": "text", "text": "x" * MAX_TEXT_LEN},
        {"type": "retype_text", "text": "a" * (MAX_TOTAL_TEXT - MAX_TEXT_LEN)},
        {"type": "retype_rules", "items": ["r"]},
    ])
    raw = [
        {"type": "retype_text", "text": "x" * MAX_TEXT_LEN},
        {"type": "retype_rules", "items": ["q" * 200] * 30},
        {"type": "retype_text", "text": "y" * MAX_TEXT_LEN},
    ]
    actual = config.sanitize_blocks(raw)
    total = sum(
        len(block["text"]) if block["type"] == "retype_text" else sum(map(len, block["items"]))
        for block in actual
    )
    assert total <= MAX_TOTAL_TEXT
    assert len(actual[1]["items"]) <= config.MAX_ITEMS


def test_retype_budget_does_not_erase_saved_ordinary_text():
    original = [
        {"type": "text", "style": "body", "text": "Introdução"},
        {"type": "retype_rules", "title": "", "items": ["Regra um", "Regra dois"]},
    ]
    assert config.sanitize_blocks(original) == original
