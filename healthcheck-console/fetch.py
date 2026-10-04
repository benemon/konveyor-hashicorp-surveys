import re
import urllib.request
from pathlib import Path

HDS = "6.6.0"
# Flight icons use currentColor; the product marks carry their brand colours.
ICONS = [
    "hashicorp-24",
    "terraform-color-24",
    "packer-color-24",
    "vault-color-24",
    "boundary-color-24",
    "consul-color-24",
    "nomad-color-24",
    "check-circle-fill-24",
    "alert-diamond-fill-24",
    "info-24",
    "loading-24",
    "external-link-16",
    "download-16",
    "trash-16",
    "reload-16",
    "play-16",
]

urllib.request.urlretrieve(
    f"https://unpkg.com/@hashicorp/design-system-components@{HDS}/dist/styles/@hashicorp/design-system-components.css",
    "hds.css",
)
symbols = []
for name in ICONS:
    svg = urllib.request.urlopen(f"https://unpkg.com/@hashicorp/flight-icons/svg/{name}.svg").read().decode()
    body = re.search(r"<svg[^>]*>(.*)</svg>", svg, re.S).group(1)
    size = name.rsplit("-", 1)[1]
    symbols.append(f'<symbol id="{name}" viewBox="0 0 {size} {size}" fill="none">{body}</symbol>')
Path("icons.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg">' + "".join(symbols) + "</svg>")
