# Ad and tracking hosts eBay pages call. The tests need none of them, and waiting on them is most of a page's load
# time. eBay's own hosts, bot detection and reCAPTCHA stay off the list.
AD_HOSTS = [
    "adtrafficquality.google",
    "casalemedia.com",
    "criteo.com",
    "doubleclick.net",
    "ebayadservices.com",
    "facebook.com",
    "facebook.net",
    "googlesyndication.com",
    "googletagmanager.com",
    "openx.net",
    "pinimg.com",
    "pinterest.com",
    "pubmatic.com",
    "reddit.com",
    "redditstatic.com",
    "rubiconproject.com",
    "sc-static.net",
    "snapchat.com",
    "tapad.com",
    "tiqcdn.com",
    "yahoo.com",
]


def block_ads_arg() -> str:
    """Chromium flag that makes AD_HOSTS and their subdomains fail to resolve, so their requests end at once.
    Unlike Playwright's request routing, this keeps the browser's HTTP cache on."""
    rules = ", ".join(f"MAP {host} ~NOTFOUND, MAP *.{host} ~NOTFOUND" for host in AD_HOSTS)
    return f"--host-resolver-rules={rules}"
