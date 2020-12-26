#!/usr/bin/env python3

from argparse import ArgumentParser
from asyncio import run as asyncio_run

from httpx import AsyncClient

from github_email_addresses import obtain_github_authors


class GithubEmailAddressesArgumentParser(ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_argument(
            'auth_username',
            help='The username of the user with which to authenticate.'
        )

        self.add_argument(
            'auth_access_token',
            help='The access token of the user with which to authenticate.'
        )

        self.add_argument(
            'repo_user',
            help='The username of the Github user whose repositories to scan.'
        )

        self.add_argument(
            '--num-max-concurrent',
            help='The maximum number of concurrent HTTP requests.',
            type=int,
            default=5
        )


async def main():

    args = GithubEmailAddressesArgumentParser().parse_args()

    client_options = dict(
        base_url='https://api.github.com/',
        headers={
            'Accept': 'application/vnd.github.v3+json'
        },
        auth=(args.auth_username, args.auth_access_token)
    )
    async with AsyncClient(**client_options) as client:
        print(
            '\n'.join(
                sorted(
                    str(commit_author)
                    for commit_author in await obtain_github_authors(
                        client=client,
                        username=args.repo_user,
                        num_max_concurrent=args.num_max_concurrent
                    )
                )
            )
        )


if __name__ == '__main__':
    asyncio_run(main())
