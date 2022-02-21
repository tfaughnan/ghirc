# ghirc

IRC bot for GitHub webhooks.

## Dependencies

- [Python 3.10+](https://docs.python.org/3/whatsnew/3.10.html)
    - for those brand-new [match statements](https://www.python.org/dev/peps/pep-0634/)
- [tomli](https://github.com/hukkin/tomli)
    - for configuration parsing
    - [there's a chance](https://www.python.org/dev/peps/pep-0680/) this joins the standard library!
- [Uvicorn](https://www.uvicorn.org/)
    - for the [ASGI](https://asgi.readthedocs.io/en/latest/) backend

## Configuration

Generate a [secret token](https://docs.github.com/en/developers/webhooks-and-events/webhooks/securing-your-webhooks).
Here is one way to do this:

```
$ python3 -c 'import secrets; print(secrets.token_hex(20))'
```

Create a config file at `~/.config/ghirc.toml` (or anywhere, if you use the `-c` flag). For example:

```
[uvicorn]
host = "127.0.0.1"
port = 1337

[github]
secret = "0a04e05d0d7dc693ad3974c5abd8a98a0d4969ac"
events = ["create", "delete", "fork", "issue_comment", "issues",
          "ping", "pull_request", "push", "star"]

[irc]
host = "irc.libera.chat"
port = 6697
ssl = true
nickname = "ghirc"
realname = "https://github.com/tfaughnan/ghirc"
channels = []
```

Not all event possible event types are supported yet, just the most desirable ones.

Finally, [create webhooks](https://docs.github.com/en/developers/webhooks-and-events/webhooks/creating-webhooks)
for your GitHub repositories. Set the payload URL to `<your-domain>/webhooks`, select `application/json`
for content type, and input the secret you generated above.


## Execution

The most basic way to run the bot is:

```
$ ./ghirc
```

There are other factors to consider when deploying ghirc.
For example, you way wish to run it behind a reverse proxy or with a process manager.
See [Uvicorn's documentation](https://www.uvicorn.org/deployment/) on this subject.
