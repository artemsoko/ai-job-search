from game.adapters.cli import main


def test_cli_runs_and_reports(capsys):
    assert main(["--script", "rock,paper", "--seed", "1"]) == 0
    out = capsys.readouterr().out
    assert "round 1:" in out and "result:" in out


def test_cli_rejects_unknown_move(capsys):
    assert main(["--script", "banana"]) == 2
    assert "error:" in capsys.readouterr().err


def test_cli_seed_makes_output_reproducible(capsys):
    main(["--rounds", "4", "--seed", "7"])
    first = capsys.readouterr().out
    main(["--rounds", "4", "--seed", "7"])
    assert capsys.readouterr().out == first
