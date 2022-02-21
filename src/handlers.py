async def create(payload, fmt):
    repo = payload["repository"]["name"]
    user = payload["sender"]["login"]
    ref_type = payload["ref_type"]
    ref = payload["ref"]
    url = payload["repository"]["html_url"]

    match ref_type:
        case "branch":
            url += f"/tree/{ref}"
        case "tag":
            url += f"/releases/tag/{ref}"

    repo = f"{fmt['color']}{fmt['black']},{fmt['yellow']}{repo}{fmt['color']}"
    user = f"{fmt['bold']}{user}{fmt['bold']}"
    msg = f"{repo}: {user} created {ref_type} {ref} @ {url}"
    return msg


async def delete(payload, fmt):
    repo = payload["repository"]["name"]
    user = payload["sender"]["login"]
    ref_type = payload["ref_type"]
    ref = payload["ref"]
    url = payload["repository"]["html_url"]

    match ref_type:
        case "branch":
            url += "/branches"
        case "tag":
            url += "/tags"

    repo = f"{fmt['color']}{fmt['black']},{fmt['yellow']}{repo}{fmt['color']}"
    user = f"{fmt['bold']}{user}{fmt['bold']}"
    msg = f"{repo}: {user} deleted {ref_type} {ref} @ {url}"
    return msg


async def fork(payload, fmt):
    repo = payload["repository"]["name"]
    user = payload["sender"]["login"]
    url = payload["forkee"]["html_url"]

    repo = f"{fmt['color']}{fmt['black']},{fmt['yellow']}{repo}{fmt['color']}"
    user = f"{fmt['bold']}{user}{fmt['bold']}"
    msg = f"{repo}: {user} forked repo @ {url}"
    return msg


# despite GH's naming, this event type is for comments on issues _and_ PRs
async def issue_comment(payload, fmt):
    repo = payload["repository"]["name"]
    user = payload["sender"]["login"]
    number = payload["issue"]["number"]
    url = payload["comment"]["html_url"]

    match payload["action"]:
        case "created":
            body = payload["comment"]["body"]
            body = body if len(body) <= 32 else body[:32] + "..."
            verb = f'commented "{body}"'
        case "edited":
            verb = "edited a comment"
        case "deleted":
            verb = "deleted a comment"

    repo = f"{fmt['color']}{fmt['black']},{fmt['yellow']}{repo}{fmt['color']}"
    user = f"{fmt['bold']}{user}{fmt['bold']}"
    msg = f"{repo}: {user} {verb} on #{number} @ {url}"
    return msg


async def issues(payload, fmt):
    repo = payload["repository"]["name"]
    user = payload["sender"]["login"]
    number = payload["issue"]["number"]
    title = payload["issue"]["title"]
    title = title if len(title) <= 32 else title[:32] + "..."
    url = payload["issue"]["html_url"]

    match payload["action"]:
        case "opened":
            verb = "opened"
        case "edited":
            verb = "edited"
        case "deleted":
            verb = "deleted"
        case "closed":
            verb = "closed"
        case "reopened":
            verb = "reopened"
        case _:  # some other action we haven't implemented yet
            return None

    repo = f"{fmt['color']}{fmt['black']},{fmt['yellow']}{repo}{fmt['color']}"
    user = f"{fmt['bold']}{user}{fmt['bold']}"
    msg = f'{repo}: {user} {verb} issue #{number} "{title}" @ {url}'
    return msg


async def ping(payload, fmt):
    repo = payload["repository"]["name"]
    user = payload["sender"]["login"]
    hook_id = payload["hook_id"]

    repo = f"{fmt['color']}{fmt['black']},{fmt['yellow']}{repo}{fmt['color']}"
    user = f"{fmt['bold']}{user}{fmt['bold']}"
    msg = f"{repo}: {user} created a webhook with id={hook_id}"
    return msg


async def pull_request(payload, fmt):
    repo = payload["repository"]["name"]
    user = payload["sender"]["login"]
    number = payload["pull_request"]["number"]
    title = payload["pull_request"]["title"]
    title = title if len(title) <= 32 else title[:32] + "..."
    url = payload["pull_request"]["html_url"]

    match payload["action"]:
        case "opened":
            verb = "opened"
        case "edited":
            verb = "edited"
        case "closed":
            verb = "merged" if payload["pull_request"]["merged"] else "closed"
        case "reopened":
            verb = "reopened"
        case "synchronize":
            verb = "synchronized"
        case _:  # some other action we haven't implemented yet
            return None

    repo = f"{fmt['color']}{fmt['black']},{fmt['yellow']}{repo}{fmt['color']}"
    user = f"{fmt['bold']}{user}{fmt['bold']}"
    msg = f'{repo}: {user} {verb} PR #{number} "{title}" @ {url}'
    return msg


async def push(payload, fmt):
    # create and delete events will already be triggered, so why bother
    if payload["created"] or payload["deleted"]:
        return None

    repo = payload["repository"]["name"]
    user = payload["sender"]["login"]
    verb = "force-pushed" if payload["forced"] else "pushed"
    ref = payload["ref"]
    url = payload["compare"]

    repo = f"{fmt['color']}{fmt['black']},{fmt['yellow']}{repo}{fmt['color']}"
    user = f"{fmt['bold']}{user}{fmt['bold']}"
    msg = f"{repo}: {user} {verb} {ref} @ {url}"
    return msg


async def star(payload, fmt):
    repo = payload["repository"]["name"]
    user = payload["sender"]["login"]
    url = payload["repository"]["html_url"] + "/stargazers"

    match payload["action"]:
        case "created":
            verb = "starred"
        case "deleted":
            verb = "unstarred"

    repo = f"{fmt['color']}{fmt['black']},{fmt['yellow']}{repo}{fmt['color']}"
    user = f"{fmt['bold']}{user}{fmt['bold']}"
    msg = f"{repo}: {user} {verb} repo @ {url}"
    return msg
