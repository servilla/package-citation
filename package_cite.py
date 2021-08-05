#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
:Mod: package_cite.py

:Synopsis:

:Author:
    servilla

:Created:
    8/5/21
"""
import logging
import os

import click
import daiquiri
from lxml import etree
import requests

cwd = os.path.dirname(os.path.realpath(__file__))
logfile = cwd + "/package_cite.log"
daiquiri.setup(level=logging.INFO,
               outputs=(daiquiri.output.File(logfile), "stdout",))
logger = daiquiri.getLogger(__name__)


def get_num(solr: str) -> str:
    solr_url = f"https://pasta.lternet.edu/package/search/eml?{solr}start=0&rows=1"
    r = requests.get(solr_url)
    r.raise_for_status()

    result_set = etree.fromstring(r.text.encode("utf-8"))
    return result_set.get("numFound")


def get_revisions(pids: list) -> list:
    pasta_url = "https://pasta.lternet.edu/package/eml/"
    package_ids = list()
    for pid in pids:
        scope, identifier, revision = pid.split(".")
        url = pasta_url + f"{scope}/{identifier}"
        r = requests.get(url)
        r.raise_for_status()
        revisions = r.text.split("\n")
        for revision in revisions:
            package_ids.append(f"{scope}.{identifier}.{revision}")
    return package_ids


help_style = "The format style of the citation (defaults to ESIP)."
help_revisions = "Include all revisions for each data package series."
help_file = "Output citations to file with name."
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument("solr", required=True)
@click.option("-s", "--style", default="ESIP", help=help_style)
@click.option("-r", "--revisions", is_flag=True, default=False, help=help_revisions)
@click.option("-f", "--file", is_flag=True, default=False, help=help_file )
def main(solr: str, style: str, revisions: bool, file: str):
    """
        Generate a list of PASTA data package citations for a specific Solr query string

        \b
            SOLR: PASTA's Solr search query string
    """
    numfound = get_num(solr)
    solr_url = f"https://pasta.lternet.edu/package/search/eml?{solr}start=0&rows={numfound}"
    r = requests.get(solr_url)
    r.raise_for_status()
    result_set = etree.fromstring(r.text.encode("utf-8"))
    pids = result_set.findall("./document/packageid")
    package_ids = list()
    for pid in pids:
        package_ids.append(pid.text)

    if revisions:
        package_ids = get_revisions(package_ids)

    citations = list()
    for package_id in package_ids:
        cite_url = f"https://cite.edirepository.org/cite/{package_id}"
        r = requests.get(cite_url)
        r.raise_for_status()
        citations.append(r.text)

    if file:
        with open("citations.txt", "w") as f:
            for citation in citations:
                f.write(citation + "\n")
    else:
        for citation in citations:
            print(citation)

    return 0


if __name__ == "__main__":
    main()
