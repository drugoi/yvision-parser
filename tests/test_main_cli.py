import pytest

import main as main_mod


def test_parse_args_account_and_default_output():
    args = main_mod.parse_args(["drugoi"])
    assert args.account == "drugoi"
    assert args.output == "posts"


def test_parse_args_custom_output():
    args = main_mod.parse_args(["8249", "--output", "/tmp/export"])
    assert args.account == "8249"
    assert args.output == "/tmp/export"


def test_account_is_required():
    with pytest.raises(SystemExit):
        main_mod.parse_args([])
