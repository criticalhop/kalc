# kalc, the Kubernetes calculator

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0) [![PyPI version](https://badge.fury.io/py/kubectl-val.svg)](https://badge.fury.io/py/kalc) [![Build Status](https://travis-ci.org/criticalhop/kalc.svg?branch=master)](https://travis-ci.org/criticalhop/kalc)

# Overview

`kalc` is application aware Kubernetes rebalancing tool built on pure [AI planning](https://github.com/criticalhop/poodle).

# Quick Start

## Requirements

- Linux x86_64
- Python 3.7+
- 6+ GB RAM, decent CPU
- Up to 20GB of disk space in `/tmp` for generated models
- `kubectl` installed and connected to cluster

## Installation

    pip install kalc
    
If your Linux host has other versions of Python installed you will recieve an error regarding "Could not find a version that satisfies the requirement kalc (from versions: )No matching distribution found for kalc"... If you recieve this, type the following to install kalc
    
    python3.7 -m pip install kalc

## Basic usage

    $ kalc-optimize

`kalc-optimize` will generate `bash` scripts containing `kubectl` commands to get to more optimal states. Have a look at those scripts and execute any one of them, then stop and re-run `kalc-optimize`.

## Autopilot

`kalc` can optimize your cluster in background, gradually increasing reliability by rebalancing and reducing cost by freeing nodes with low utilization. You can run `kalc-optimize` as a cron job, wait for X minutes and then run the most recent generated script file.

# Architecture

- `kalc-optimize` will download current cluster state by executing `kubectl get all` and will start generating `bash` scripts into current folder
- Each generated `bash` script contains a sequence of `kubectl` commands to get the cluster in a more optimal state: better balanced nodes for availability and OOM/eviction resilience and a more compact packing
- As `kalc` continues to compute, it will emit more optimal states and bigger bash scripts with kubectl commands

`kalc` aims to take into account current policies, anti-affility, SLO levels and best practices from successful production Kubernetes clusters.

# Project Status

`kalc` is a developer preview and currently supports a subset of Kubernetes resources and behaviour model.

We invite you to follow [@criticalhop](https://twitter.com/criticalhop) on [Twitter](https://twitter.com/criticalhop) and to chat with the team at `#kalc` on [freenode](https://freenode.net/). If you have any questions or suggestions - feel free to open a [github issue](https://github.com/criticalhop/kalc/issues) or contact andrew@kalc.io directly.

For enterprise enquiries, use the form on our website: [kalc.io](https://kalc.io) or write us an email at info@kalc.io
