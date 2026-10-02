import io
import platform
import tarfile
import urllib.request
import zipfile
from pathlib import Path

import summary

PANDOC = "3.12"
TECTONIC = "0.17.0"
EISVOGEL = "3.5.1"
PLEX = "1.1.0"
arm = platform.machine() == "aarch64"


def get(url):
    return io.BytesIO(urllib.request.urlopen(url).read())


def install(archive, member, target):
    Path(target).write_bytes(tarfile.open(fileobj=archive).extractfile(member).read())
    Path(target).chmod(0o755)


install(
    get(f"https://github.com/jgm/pandoc/releases/download/{PANDOC}/pandoc-{PANDOC}-linux-{'arm64' if arm else 'amd64'}.tar.gz"),
    f"pandoc-{PANDOC}/bin/pandoc",
    "/usr/local/bin/pandoc",
)
install(
    get(
        f"https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%40{TECTONIC}/"
        f"tectonic-{TECTONIC}-{'aarch64' if arm else 'x86_64'}-unknown-linux-musl.tar.gz"
    ),
    "tectonic",
    "/usr/local/bin/tectonic",
)
template = tarfile.open(
    fileobj=get(f"https://github.com/Wandmalfarbe/pandoc-latex-template/releases/download/v{EISVOGEL}/Eisvogel.tar.gz")
)
Path(summary.TEMPLATE).write_bytes(
    template.extractfile(next(m for m in template.getmembers() if m.name.endswith("eisvogel.latex"))).read()
)
fonts = zipfile.ZipFile(get(f"https://github.com/IBM/plex/releases/download/%40ibm%2Fplex-sans%40{PLEX}/ibm-plex-sans.zip"))
Path("/usr/share/fonts/plex").mkdir(parents=True)
for name in fonts.namelist():
    if name.endswith(".otf") and "/complete/otf/" in name:
        Path("/usr/share/fonts/plex", name.rsplit("/", 1)[1]).write_bytes(fonts.read(name))

# Tectonic downloads the TeX files a document needs on first use. Rendering a summary that
# uses every construct here puts them in the image, so the addon needs no network.
evidence = {"facet": "f", "answer": "a", "rationale": "r", "mitigation": "m"}
summary.pdf(
    "Example",
    {
        "generated": "2026-01-01T00:00:00+00:00",
        "questionnaire_version": "0",
        "environment": "e",
        "verdict": "v",
        "areas": [{"capability": "Human Access", "strength": "strong", "evidence": [evidence]}],
        "in_good_shape": ["Workload Lifecycle"],
        "patterns": [{"name": "n", "detail": "d"}],
        "unknowns": [{"question": "q"}],
        "implementation": None,
    },
    cached=False,
)
