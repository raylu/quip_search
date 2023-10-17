#!/usr/bin/env python3

import datetime
import pathlib

import click
import httpx

@click.command()
@click.argument('query', nargs=-1, required=True)
@click.option('--limit', '-l', type=int, default=50)
@click.option('--body', '-b', is_flag=True, help='otherwise, only search titles')
def main(query: str, limit: int, body: bool) -> None:
	"""searches quip"""
	current_dir = pathlib.Path(__file__).resolve().parent
	try:
		access_token = (current_dir / 'access_token').read_text().rstrip()
	except FileNotFoundError:
		click.echo('go to ' + click.style('https://quip.com/dev/token', fg='bright_blue'))
		click.echo('paste the result into `access_token`')
		raise click.Abort

	# https://quip.com/dev/automation/documentation/current#operation/searchForThreads
	response = httpx.get('https://platform.quip.com/1/threads/search',
			headers={'Authorization': 'Bearer ' + access_token},
			params={'query': query, 'count': limit, 'only_match_titles': not body})
	response.raise_for_status()

	for data in response.json():
		thread = data['thread']
		click.secho(thread['title'], fg='green')
		click.echo('\tcreated: ' + datetime.datetime.fromtimestamp(thread['created_usec'] / 1000000).isoformat())
		click.echo('\tupdated: ' + datetime.datetime.fromtimestamp(thread['updated_usec'] / 1000000).isoformat())
		click.secho('\t' + thread['link'], fg='bright_black')
		click.echo()

if __name__ == '__main__':
	main()
