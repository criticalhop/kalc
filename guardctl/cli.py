import click
import os 

@click.group()
def cli():
    pass

@click.command()
@click.option("--test-cluster", "-c", help="Directory with cluster resources definitions", type=str, required=True)
@click.option("--out-format", "-o", help="Select output format", type=str, required=False)
@click.option("-f", help="Create new resource from YAML file", type=str, required=False, multiple=True)
def test(test, test_cluster, f):
    c = KubenetesCluster()

    click.echo(f"Loading cluster definitions from {test_cluster} ...")
    for root, dirs, files in os.walk(test_cluster):
        for fn in files: 
            click.echo(f" ... {fn}")
            c.load_state(open(os.path.join(root, fn)).read())

    c.build_state()

    for res in f: 
        click.echo(f"Creating resource from {f}")
        c.create_resource(open(res).read())

    scenario = c.run()

    if scenario: click.echo(scenario.yaml())
    else: click.echo("Cluster clean!")

@click.command()
@click.option("-f", help="Create new resource from YAML file", type=str, required=False, multiple=True)
def run(f):
    c = KubenetesCluster()

    click.echo("Fetching cluster state ...")

    c.fetch_state_default()

    c.build_state()

    scenario = c.run()

    if scenario: click.echo(scenario.yaml())
    else: click.echo("Cluster clean!")

cli.add_command(test)
cli.add_command(run)