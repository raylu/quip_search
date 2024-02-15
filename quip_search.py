#!/usr/bin/env python3

import datetime
import json
import pathlib

import click
import httpx

@click.command()
@click.argument('query', nargs=-1, required=True)
@click.option('--limit', '-l', type=int, default=50)
@click.option('--body', '-b', is_flag=True, help='otherwise, only search titles')
@click.option('--alfred', is_flag=True, help='format for alfred script filter')
def main(query: tuple[str], limit: int, body: bool, alfred: bool) -> None:
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
			params={'query': ' '.join(query), 'count': limit, 'only_match_titles': not body})
	response.raise_for_status()

	if alfred:
		items = []
		for data in response.json():
			thread = data['thread']
			items.append({
				'title': thread['title'],
				'subtitle': f'updated: {format_usec(thread["updated_usec"])}',
				'arg': thread['link'],
			})
		click.echo(json.dumps({'items': items}))
	else:
		for data in response.json():
			thread = data['thread']
			click.secho(thread['title'], fg='green')
			click.echo('\tcreated: ' + format_usec(thread['created_usec']))
			click.echo('\tupdated: ' + format_usec(thread['updated_usec']))
			click.secho('\t' + thread['link'], fg='bright_black')
			click.echo()

def format_usec(ts_usec: int) -> str:
	return datetime.datetime.fromtimestamp(ts_usec / 1000000).isoformat()

if __name__ == '__main__':
	main()
