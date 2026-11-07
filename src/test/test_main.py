from hebrewenglish.main import parse_args


def test_defaults_serve_on_every_address_at_8080(monkeypatch):
    monkeypatch.delenv("PORT", raising=False)
    args = parse_args([])
    assert (args.host, args.port, args.show) == ("0.0.0.0", 8080, True)


def test_url_can_be_chosen():
    args = parse_args(["--host", "127.0.0.1", "--port", "8090", "--no-show"])
    assert (args.host, args.port, args.show) == ("127.0.0.1", 8090, False)


def test_a_container_host_chooses_the_port_through_the_environment(monkeypatch):
    monkeypatch.setenv("PORT", "7860")
    assert parse_args([]).port == 7860
    # An explicit --port still wins
    assert parse_args(["--port", "8090"]).port == 8090
