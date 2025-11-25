#! /usr/bin/env python
import logging

import click

from ij_open_data.constants import LOG_LEVEL
from ij_open_data.scrap_open_data_cnam_ij import (
    clean_data_cnam,
    scrap_ameli_for_ij,
)

logging.basicConfig(
    level=logging.getLevelName(LOG_LEVEL),
    format="%(asctime)s %(name)-12s %(levelname)-8s %(message)s",
)


@click.group()
@click.version_option(package_name="ij_open_data")
def cli():
    pass


@cli.command()
def get_open_data_cnam() -> None:
    """Télécharge les données IJ de la CNAM, les nettoie et les sauvegarde au format parquet."""
    scrap_ameli_for_ij()
    clean_data_cnam()


if __name__ == "__main__":
    cli()
