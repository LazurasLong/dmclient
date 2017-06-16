"""The (probably bulk?) aspect of dmclient's searching.

Provides a means to index PDFs.

"""
import io
import logging

import pdfminer
import pdfminer.high_level
import pdfminer.layout
from pdfminer.image import ImageWriter

from oracle.provider import FileProvider

log = logging.getLogger(__name__)


# pdfminer sometimes gets it wrong, so we need to guide its substitution.
# letters that look similar that it gets wrong:
#   5 -> s
#   1 -> t, l, variety of things...
#
# need to fix autocorrect too:
#   it loves to turn d4, d6, etc into junk
#
# also, single punctuation does stupid things: & spellchecked to a

def pdf_text(file, outfile):
    no_laparams = False
    all_texts = None
    detect_vertical = None
    word_margin = None
    char_margin = None
    line_margin = None
    boxes_flow = None
    output_type = 'text'
    codec = 'utf-8'
    strip_control = False
    maxpages = 0
    page_numbers = None
    password = ""
    scale = 1.0
    rotation = 0
    layoutmode = 'normal'
    output_dir = None
    debug = False
    disable_caching = False

    # If any LAParams group arguments were passed, create an LAParams object and
    # populate with given args. Otherwise, set it to None.
    if not no_laparams:
        laparams = pdfminer.layout.LAParams()
        for param in (
                "all_texts", "detect_vertical", "word_margin", "char_margin",
                "line_margin", "boxes_flow"):
            paramv = locals().get(param, None)
            if paramv is not None:
                setattr(laparams, param, paramv)
    else:
        laparams = None

    imagewriter = None
    if output_dir:
        imagewriter = ImageWriter(output_dir)

    pdfminer.high_level.extract_text_to_fp(file, outfile, **locals())


class PdfProvider(FileProvider):
    def index_file_contents(self, path):
        with open(path, 'rb') as f:
            text = self.pdf_text(f)
        return self.spellchecked(text)

    def pdf_text(self, pdffile):
        of = io.StringIO()
        log.debug("pdf2txt-ing `%s'...", pdffile.name)
        pdf_text(pdffile, of)
        return of.getvalue()

    def spellchecked(self, text):
        # TODO: Why does this strip punctuation? Does it matter?
        import autocorrect
        buf = io.StringIO()
        for line in text.split('\n'):
            for word in line.split(' '):
                # Not sure why, but blank lines/words are turned into `a'.
                if not word:
                    continue
                new_word = autocorrect.spell(word)
                log.debug("%s spellchecked to %s", word, new_word)
                buf.write(new_word)
                buf.write(' ')
            buf.write('\n')
        return buf.getvalue()


def main():
    import argparse
    argparser = argparse.ArgumentParser()
    argparser.add_argument("--disable-spellcheck", action='store_true',
                           help="Skip spell-correcting the mined text.")
    argparser.add_argument("file", type=argparse.FileType('rb'),
                           help="PDF file to extract text from.")
    argparser.add_argument("outfile", type=argparse.FileType('w'),
                           help="File to output plaintext to.")
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("pdfminer").setLevel(logging.ERROR)
    args = argparser.parse_args()

    p = PdfProvider()

    log.info("begin text extraction")
    text = p.pdf_text(args.file)
    if not args.disable_spellcheck:
        log.info("begin spellcheck")
        text = str(p.spellchecked(text))
    print(text, file=args.outfile)

    log.info("done")


if __name__ == '__main__':
    main()
