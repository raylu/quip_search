#!/usr/bin/env python3

import base64
import datetime
import json
import shutil
import struct
import subprocess
import textwrap

import click
import httpx

@click.command()
@click.argument('query', nargs=-1, required=True)
@click.option('--limit', '-l', type=int, default=50)
@click.option('--body', '-b', is_flag=True, help='otherwise, only search titles')
@click.option('--alfred', is_flag=True, help='format for alfred script filter')
def main(query: tuple[str], limit: int, body: bool, alfred: bool) -> None:
	"""searches confluence"""
	username = get_1pass('op://Private/confluence token/username')
	confluence_token = get_1pass('op://Private/confluence token/credential')

	# https://developer.atlassian.com/cloud/confluence/rest/v1/api-group-search/
	joined_query = ' '.join(query)
	cql = f'type=page AND title~"{joined_query}"'
	if body:
		cql = f'({cql} OR text~"{joined_query}")'
	cql = 'type=page AND ' + cql
	response = httpx.get('https://benchling.atlassian.net/wiki/rest/api/search',
			auth=httpx.BasicAuth(username, confluence_token),
			params={'cql': cql, 'limit': limit})
	response.raise_for_status()
	results = response.json()['results']

	if alfred:
		items = []
		for page in results:
			page_id = int(page['content']['id'])
			# stolen from https://confluencer.readthedocs.io/en/latest/_modules/confluencer/api.html
			tiny_id = base64.b64encode(struct.pack('<L', page_id).rstrip(b'\0'), altchars=b'_-').rstrip(b'=')
			items.append({
				'title': page['content']['title'],
				'subtitle': page['excerpt'].replace('\n', '  '),
				'arg': 'https://benchling.atlassian.net/wiki/x/' + tiny_id.decode('ascii'),
			})
		click.echo(json.dumps({'items': items}))
	else:
		for page in results:
			click.secho(page['content']['title'], fg='green')
			excerpt, _, start = page['excerpt'].partition('@@@hl@@@')
			if len(start) > 0:
				highlight, _, rest = start.partition('@@@endhl@@@')
				excerpt += click.style(highlight, fg='cyan') + rest
			excerpt = '\n'.join(textwrap.wrap(excerpt, shutil.get_terminal_size().columns - 8))
			click.echo(textwrap.indent(excerpt, '\t'))
			click.secho('\tupdated: ' + page['friendlyLastModified'], fg='blue')
			click.secho('\thttps://benchling.atlassian.net/wiki' + page['url'], fg='bright_black')
			click.echo()

def get_1pass(field: str) -> str:
	onepass = subprocess.run(['op', 'read', field], capture_output=True, encoding='ascii', check=True)
	return onepass.stdout.rstrip()

if __name__ == '__main__':
	main()
