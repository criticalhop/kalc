import click
import logging
import os
import sys
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.search import AnyServiceInterrupted 
from guardctl.model.scenario import Scenario
from yaspin import yaspin
from yaspin.spinners import Spinners
from sys import stdout
from guardctl.model.search import ExcludeDict, mark_excluded
from guardctl.model.system.primitives import TypeServ
from pyupdater.client import Client
from guardctl.misc.client_config import ClientConfig
import poodle
poodle.log.setLevel(logging.ERROR)

APP_NAME = 'kubectl-sim'
APP_VERSION = '0.1.3'

@click.group(invoke_without_command=True)
@click.version_option(version=APP_VERSION)
@click.option("--from-dir", "-d", help="Directory with cluster resources definitions", \
                type=str, required=True)
@click.option("--output", "-o", help="Select output format", \
                type=click.Choice(["yaml"]), required=False, default="yaml")
@click.option("--filename", "-f", help="Create new resource from YAML file", \
                type=str, required=False, multiple=True)
@click.option("--timeout", "-t", help="Set AI planner timeout in seconds", \
                type=int, required=False, default=150)
@click.option("--exclude", "-e", help="Exclude from search <Kind1>:<name1>,<Kind2>:<name2>,...", \
                required=False, default=None)
@click.option("--ignore-nonexistent-exclusions", \
    help="Ignore mistyped/absent exclusions from --exclude", type=bool, \
                            is_flag=True, required=False, default=False)
@click.option("--pipe", help="Terse mode to reduce verbosity for shell piping", \
                    type=bool, is_flag=True, required=False, default=False)
def run(from_dir, output, filename, timeout, exclude, ignore_nonexistent_exclusions, pipe):

    k = KubernetesCluster()

    click.echo(f"# Loading cluster definitions from {from_dir} ...")
    k.load_dir(from_dir)

    for f in filename:
        click.echo(f"# Creating resource from {f} ...")
        k.create_resource(open(f).read())

    click.echo(f"# Building abstract state ...")
    k._build_state()
    if exclude != None:
        excludeList = []
        for kn in exclude.split(","):
            click.echo(f"# Exclude {kn} ...")
            excludeList.append(ExcludeDict(kn))
        mark_excluded(k.state_objects, excludeList, ignore_nonexistent_exclusions)
    p = AnyServiceInterrupted(k.state_objects)
    # p.select_target_service()

    click.echo("# Solving ...")

    if stdout.isatty() and not pipe:
        with yaspin(Spinners.earth, text="") as sp:
            p.run(timeout=timeout, sessionName="cli_run")
            if not p.plan:
                sp.ok("✅ ")
                click.echo("# No scenario was found.")
            else:
                sp.fail("💥 ")
                click.echo("# Scenario found.")
                click.echo(Scenario(p.plan).asyaml())
    else:
        p.run(timeout=timeout, sessionName="cli_run")
        click.echo(Scenario(p.plan).asyaml())

def print_status_info(info):
    total = info.get(u'total')
    downloaded = info.get(u'downloaded')
    status = info.get(u'status')
    # print("#", downloaded, total, status)
    click.echo("#", downloaded, total, status)

if getattr(sys, 'frozen', False):
    sys.argv[0] = "kubectl-sim"
    if "--debug-updater" in sys.argv:
        logging.getLogger("pyupdater").setLevel(logging.DEBUG)
        STDERR_HANDLER = logging.StreamHandler(sys.stderr)
        STDERR_HANDLER.setFormatter(logging.Formatter(logging.BASIC_FORMAT))
        logging.getLogger("pyupdater").addHandler(STDERR_HANDLER)
    else:
        logging.getLogger("pyupdater").setLevel(logging.ERROR)
        import poodle
        poodle.log.setLevel(logging.ERROR)
    client = Client(ClientConfig())
    client.refresh()
    app_update = client.update_check(APP_NAME, APP_VERSION)
    if app_update is not None:
        app_update.download()
        if app_update.is_downloaded():
            app_update.extract_restart()
    run(sys.argv[1:]) # pylint: disable=no-value-for-parameter
