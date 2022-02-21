import asyncio
import hashlib
import hmac
import json
import re
import sys

from src import handlers


class App:
    def __init__(self, config):
        self.host = config["irc"]["host"]
        self.port = config["irc"]["port"]
        self.ssl = config["irc"]["ssl"]
        self.nickname = config["irc"]["nickname"]
        self.realname = config["irc"]["realname"]
        self.channels = config["irc"]["channels"]

        # IRC formatting per https://modern.ircdocs.horse/formatting.html
        self.formatting = {
            "bold": "\u0002",
            "color": "\u0003",
            "white": "00",
            "black": "01",
            "blue": "02",
            "green": "03",
            "red": "04",
            "brown": "05",
            "magenta": "06",
            "orange": "07",
            "yellow": "08",
            "lightgreen": "09",
            "cyan": "10",
            "lightcyan": "11",
            "lightblue": "12",
            "pink": "13",
            "grey": "14",
            "lightgrey": "15",
            "default": "99",
        }

        self.reader = None
        self.writer = None

        self.secret = config["github"]["secret"].encode()
        self.events = config["github"]["events"]
        self.event_handlers = {
            "create": handlers.create,
            "delete": handlers.delete,
            "fork": handlers.fork,
            "issue_comment": handlers.issue_comment,
            "issues": handlers.issues,
            "ping": handlers.ping,
            "pull_request": handlers.pull_request,
            "push": handlers.push,
            "star": handlers.star,
        }

        # bail out if user wants events for which we haven't written handlers
        for event in self.events:
            if event not in self.event_handlers:
                sys.exit(f"{event} is not a supported event type.")

    async def irc_connect(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.host, self.port, ssl=self.ssl
        )

        self.writer.write(f"NICK {self.nickname}\r\n".encode())
        self.writer.write(
            f"USER {self.nickname} 8 * :{self.realname}\r\n".encode()
        )
        await self.writer.drain()

        for channel in self.channels:
            self.writer.write(f"JOIN {channel}\r\n".encode())
            await self.writer.drain()

        # receive incoming IRC messages and take action if we wish
        loop = asyncio.get_event_loop()
        loop.create_task(self.irc_mainloop())

    async def irc_mainloop(self):
        while not self.writer.is_closing():
            raw_message = (await self.reader.readline()).decode().strip()
            print(raw_message)
            if m := re.match(r"^PING (?P<token>.*)$", raw_message):
                token = m.groupdict().get("token", self.nickname)
                self.writer.write(f"PONG {token}\r\n".encode())
                await self.writer.drain()

        sys.exit("IRC connection closed.")

    async def irc_chanmsg(self, message):
        for channel in self.channels:
            self.writer.write(f"PRIVMSG {channel} :{message}\r\n".encode())
            await self.writer.drain()

    async def __call__(self, scope, receive, send):
        match scope["type"]:
            case "lifespan":
                message = await receive()
                match message["type"]:
                    case "lifespan.startup":
                        await self.irc_connect()
                    case "lifespan.shutdown":
                        # TODO: await self.irc_disconnect()
                        pass

            case "http":
                await self.http(scope, receive, send)

    async def http(self, scope, receive, send):
        if scope["path"] == "/webhooks" and scope["method"] == "POST":
            headers = [(b"content-type", b"text/plain")]
            # NOTE: in general a multidict is more appropriate, but the
            # headers we care about will not be repeated so a built-in
            # dict is okay for storing req_headers
            req_headers = dict(scope["headers"])
            payload_raw = await self.read_body(receive)

            gh_signature = req_headers.get(b"x-hub-signature-256").decode()
            if await self.valid_signature(payload_raw, gh_signature):
                try:
                    payload = json.loads(payload_raw)
                    status = 202
                    body = b"Received payload successfully"

                    if (
                        event := req_headers.get(b"x-github-event").decode()
                    ) in self.events and (
                        message := (
                            await self.event_handlers[event](
                                payload, self.formatting
                            )
                        )
                    ):
                        await self.irc_chanmsg(message)
                except json.JSONDecodeError:
                    status = 400
                    body = b"Failed to parse payload as JSON"
            else:
                print("invalid signature")
                status = 401
                body = b"Invalid signature"
        else:
            status = 307
            headers = [(b"location", b"https://github.com/tfaughnan/ghirc")]
            body = None

        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": headers,
            }
        )
        await send({"type": "http.response.body", "body": body})

    async def read_body(self, receive):
        body = b""
        more_body = True

        while more_body:
            message = await receive()
            body += message.get("body", b"")
            more_body = message.get("more_body", False)

        return body

    async def valid_signature(self, payload_raw, gh_signature):
        signature = (
            "sha256="
            + hmac.HMAC(
                self.secret, msg=payload_raw, digestmod=hashlib.sha256
            ).hexdigest()
        )

        return hmac.compare_digest(signature, gh_signature)
