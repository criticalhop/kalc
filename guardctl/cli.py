import click
import os
from guardctl.model.kubernetes import KubernetesCluster

@click.group()
def cli():
    pass

@click.command()
@click.option("--from-dir", "-d", help="Directory with cluster resources definitions", type=str, required=True)
@click.option("--output", "-o", help="Select output format", type=click.Choice(["json", "yaml", "wide"]), required=False, default="wide")
@click.option("-f", help="Create new resource from YAML file", type=str, required=False, multiple=True)
def test(test, from_dir, output, f):
    c = KubernetesCluster()

    # TODO: only echo this if -o=wide
    click.echo(f"Loading cluster definitions from {from_dir} ...")

    c.load_dir(from_dir)

    for res in f:
        click.echo(f"Creating resource from {f}")
        c.create_resource(open(res).read())

    scenario = c.run()

    if scenario: click.echo(scenario.yaml())
    else: click.echo("Cluster clean!")

@click.command()
@click.option("-f", help="Create new resource from YAML file", type=str, required=False, multiple=True)
def run(f):
    c = KubernetesCluster()

    click.echo("Fetching cluster state ...")

    c.fetch_state_default()

    scenario = c.run()

    if scenario: click.echo(scenario.yaml())
    else: click.echo("Cluster clean!")

cli.add_command(test)
cli.add_command(run)
