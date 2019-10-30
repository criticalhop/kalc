import click
import logging
import os
import sys
import re
import time
import json
from collections import defaultdict
from guardctl.model.kubernetes import KubernetesCluster
from guardctl.model.search import \
            Check_services, Check_deployments, Check_daemonsets, CheckNodeOutage
from guardctl.model.scenario import Scenario
from yaspin import yaspin
from yaspin.spinners import Spinners
from sys import stdout
from guardctl.model.search import ExcludeDict, mark_excluded
from guardctl.model.system.primitives import TypeServ
from guardctl.misc.util import split_yamldumps
from pyupdater.client import Client
from guardctl.misc.client_config import ClientConfig
import guardctl.misc.util as util
import poodle
poodle.log.setLevel(logging.ERROR)

APP_NAME = 'kubectl-val'
APP_VERSION = '0.1.4'

DEFAULT_PROFILE = "Check_services"
ALL_PROFILES = [x for x in globals() if x.startswith("Check")]

@click.group(invoke_without_command=True)
@click.version_option(version=APP_VERSION)
@click.option("--load-dump", "-l", \
    help="Path for file or directory containing current state manifests dump", 
    type=click.Path(exists=True), default=None, multiple=True, required=True)
@click.option("--output", "-o", help="Select output format", \
    type=click.Choice(["yaml"]), required=False, default="yaml")
@click.option("--filename", "-f", 
    help="Create/Apply new resource from YAML files (or file paths with space separator) (select type by mode)", \
    type=click.Path(exists=True), required=False, multiple=True)
@click.option("--timeout", "-t", help="Set AI planner timeout in seconds", \
    type=int, required=False, default=150)
@click.option("--exclude", "-e", 
    help="Exclude from search <Kind1>:<name1>,<Kind2>:<name2>,...", \
    required=False, default=None)
@click.option("--ignore-nonexistent-exclusions", \
    help="Ignore mistyped/absent exclusions from --exclude", type=bool, \
    is_flag=True, required=False, default=False)
@click.option("--pipe", help="Terse mode to reduce verbosity for shell piping", \
    type=bool, is_flag=True, required=False, default=False)
@click.option("--mode", "-m", 
    help="Choose the mode scale/apply/replace/remove/create(default)", \
    required=False, default=KubernetesCluster.CREATE_MODE)
@click.option("--replicas", help="take pods amount for scale, default 5", \
    type=int, required=False, default=5)
@click.option("--profile", help="Search profile", default=DEFAULT_PROFILE, type=click.Choice(ALL_PROFILES))
def run(load_dump, output, filename, timeout, exclude, ignore_nonexistent_exclusions, pipe, mode, replicas, profile):
    run_start = time.time()

    k = KubernetesCluster()
    
    click.echo("log:")

    if load_dump:
        for df in load_dump:
            if os.path.isfile(df):
                click.echo(f"    - Loading cluster definitions from file {df} ...")
                for ys in split_yamldumps(open(df).read()):
                    k.load(ys)
            else:
                click.echo(f"    - Loading cluster definitions from folder {df} ...")
                k.load_dir(df)


    if mode == KubernetesCluster.CREATE_MODE:
        for f in filename:
            click.echo(f"    - Creating resource from {f} ...")
            k.create_resource(open(f).read())

    if mode == KubernetesCluster.APPLY_MODE:
        for f in filename:
            click.echo(f"    - Apply resource from {f} ...")
            k.apply_resource(open(f).read())

    if mode == KubernetesCluster.SCALE_MODE:
        k.scale(replicas, mode)

    click.echo(f"    - Building abstract state ...")
    k._build_state()

    stats = defaultdict(int)
    for ob in k.state_objects: stats[type(ob).__name__] += 1
    click.echo(f"    - "+json.dumps(stats))


    mark_excluded(k.state_objects, exclude, ignore_nonexistent_exclusions)

    click.echo(f"    - Using profile {profile}")
    p = globals()[str(profile)](k.state_objects)

    if timeout == 0 :
        click.echo("Skip scenario searching, timeout is 0")
    else:
        click.echo("    - Solving ...")

        search_start = time.time()

        if stdout.isatty() and not pipe:
            with yaspin(Spinners.earth, text="") as sp:
                p.run(timeout=timeout, sessionName="cli_run")
                if not p.plan:
                    sp.ok("✅ ")
                    click.echo("    - No scenario was found. Cluster clean or search timeout (try increasing).")
                else:
                    sp.fail("💥 ")
                    click.echo("    - Scenario found.")
                    click.echo(Scenario(p.plan).asyaml())
        else:
            p.run(timeout=timeout, sessionName="cli_run")
            click.echo(Scenario(p.plan).asyaml())
    click.echo("stats:")
    click.echo("    objects: %s" % len(k.state_objects))
    click.echo("    kinds: %s" % json.dumps(stats))
    click.echo("    searchSeconds: %s" % int(time.time()-search_start))
    click.echo("    runSeconds: %s" % int(time.time()-run_start))
    click.echo("    normalization:")
    click.echo("        cpu: %s" % util.CPU_DIVISOR)
    click.echo("        memory: %s" % util.MEM_DIVISOR)
    click.echo("        prio: %s" % json.dumps(util.PRIO_MAPPING))
    click.echo("        maxlin: %s" % util.POODLE_MAXLIN)

def print_status_info(info):
    total = info.get(u'total')
    downloaded = info.get(u'downloaded')
    status = info.get(u'status')
    # print("#", downloaded, total, status)
    click.echo("#", downloaded, total, status)

if getattr(sys, 'frozen', False):
    sys.argv[0] = "kubectl-val"
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
