# github_email_addresses

List the authors that appear in the commit history of a GitHub user's repositories.

The information is obtained by making requests with the [GitHub REST API](https://docs.github.com/en/rest). One must authenticate using a _personal access token_ to avoid traffic limitations. See [Creating a personal access token](https://docs.github.com/en/github/authenticating-to-github/creating-a-personal-access-token) for instructions.

Scans all branches of a repository. In case the repository is forked, only commits made after the fork date are examined.

## Usage

```
usage: github_email_addresses.py [-h] [-n NUM_MAX_CONCURRENT] [-p] auth_username auth_access_token repo_user

List the authors that appear in the commit history of a user's repositories.

positional arguments:
  auth_username         The username of the user with which to authenticate.
  auth_access_token     The access token of the user with which to authenticate.
  repo_user             The username of the GitHub user whose repositories to scan.

optional arguments:
  -h, --help            show this help message and exit
  -n NUM_MAX_CONCURRENT, --num-max-concurrent NUM_MAX_CONCURRENT
                        The maximum number of concurrent HTTP requests.
  -p, --per-repo        Show commit authors per repository.

The information is obtained by making requests with the GitHub REST API. One must authenticate using a personal access token to avoid traffic limitations.
Scans all branches of a repository. In case the repository is forked, only commits made after the fork date are examined.
```

### Example

```shell
$ ./github_email_addresses.py 'vphpersson' "$GITHUB_ACCESS_TOKEN" 'SandboxEscaper'
```

Output:
```
sandboxescaper@gmail.com SandboxEscaper
sandboxescaper@protonmail.com SandboxEscaper
```

:thumbsup:
