import io
from pypdf import PdfReader, PdfWriter
from bnf_p0.pdf_tools import download_pdf


def make_pdf(n):
    out = io.BytesIO()
    w = PdfWriter()
    for _ in range(n):
        w.add_blank_page(width=10, height=10)
    w.write(out)
    return out.getvalue()


class FakeClient:
    def __init__(self): self.calls = []
    def view_count(self, ark): return 4
    def pdf(self, ark, start_view=None, nviews=None):
        self.calls.append((start_view, nviews))
        return make_pdf(4)


def test_block_pdf_drops_repeated_cover_pages(tmp_path):
    client = FakeClient()
    out = download_pdf("bpt6kX", tmp_path / "out.pdf", start=1, end=4, block_size=2, client=client)
    reader = PdfReader(out)
    assert len(reader.pages) == 6
    assert client.calls == [(1, 2), (3, 2)]
