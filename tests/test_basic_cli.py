from guardctl.cli import run
import click
from click.testing import CliRunner
import pytest

def test_zero_invocation():
    runner = CliRunner()
    result = runner.invoke(run, [])
    global RESULT
    RESULT=result
    print(RESULT.output)
    assert not "Solving" in result.output
    assert not "Usage: kubectl-val" in result.output

def test_help_message():
    runner = CliRunner()
    result = runner.invoke(run, ["--help"])
    assert result.exit_code == 0
    global RESULT
    RESULT=result
    # print(RESULT.output)
    assert not "Usage: kubectl-val" in result.output