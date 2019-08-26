import pytest
from click.testing import CliRunner
from guardctl import cli


@pytest.fixture
def runner():
    return CliRunner()

@pytest.mark.skip(reason="no way of currently testing this")
def test_cli(runner):
    result = runner.invoke(cli.test)
    assert result.exit_code == 0
    assert not result.exception
    assert result.output.strip() == 'Hello, world.'

