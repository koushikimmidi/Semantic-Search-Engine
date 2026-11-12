import re


# Artefacts that appear in the exported knowledge-base PDFs.
_CITATION_PATTERN = re.compile(r"\[\s*cite\s*:[^\]]*\]", re.IGNORECASE)
_PAGE_FOOTER_PATTERN = re.compile(r"^\s*page\s+\d+\s+of\s+\d+\s*$", re.IGNORECASE)
_BULLET_ONLY_PATTERN = re.compile(r"^\s*[•\-\*▪●◦]+\s*$")
_BULLET_PREFIX_PATTERN = re.compile(r"^\s*[•▪●◦]\s*")

# Split after . ! ? when followed by whitespace and an uppercase
# letter, digit, quote or bracket.
_SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[])")

_TERMINAL_PUNCTUATION = (".", "!", "?", ":", ";", ",")


def clean_document_text(text):
    """
    Remove export artefacts (citation markers, page footers, empty
    bullet lines) while keeping the line structure.
    """

    if not text:
        return ""

    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _CITATION_PATTERN.sub("", text)

    lines = []

    for line in text.split("\n"):

        if _PAGE_FOOTER_PATTERN.match(line):
            continue

        if _BULLET_ONLY_PATTERN.match(line):
            continue

        line = _BULLET_PREFIX_PATTERN.sub("", line)
        line = re.sub(r"[ \t]+", " ", line).strip()
        # "request a refund ." -> "request a refund."
        line = re.sub(r"\s+([.,;:!?])", r"\1", line)

        lines.append(line)

    # Join "Label:" lines with the value on the next line, e.g.
    # "Policy ID:" + "EA-POL-001" -> "Policy ID: EA-POL-001".
    joined = []

    for line in lines:

        if (
            joined
            and line
            and joined[-1].endswith(":")
            and len(joined[-1]) <= 40
            and len(line) <= 60
        ):
            joined[-1] = f"{joined[-1]} {line}"
        else:
            joined.append(line)

    return "\n".join(joined)


class TextChunker:
    """
    Sentence-aware chunker.

    1. Cleans the text and rebuilds paragraphs from wrapped lines.
    2. Detects short title-like lines as section headings.
    3. Packs whole sentences into chunks of at most `chunk_size`
       characters, repeating the last `overlap_sentences`
       sentences at the start of the next chunk.
    4. Prefixes each chunk with its section heading so a chunk
       still makes sense on its own.

    `overlap` (characters) is accepted for backwards compatibility
    and converted to a sentence overlap.
    """

    # Bump when the chunking logic changes (invalidates caches).
    VERSION = 2

    def __init__(
        self,
        chunk_size=700,
        overlap=None,
        overlap_sentences=1,
        heading_max_length=70
    ):

        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        self.chunk_size = chunk_size

        if overlap is not None:
            overlap_sentences = 1 if overlap > 0 else 0

        self.overlap_sentences = max(0, overlap_sentences)
        self.heading_max_length = heading_max_length

    # ========================================================
    # STRUCTURE
    # ========================================================

    def _is_heading(self, line):

        if not line or len(line) > self.heading_max_length:
            return False

        if line.endswith(_TERMINAL_PUNCTUATION):
            return False

        # Needs at least one letter, e.g. "2. Refund Eligibility".
        return bool(re.search(r"[A-Za-z]", line))

    def _sections(self, text):
        """
        Return [(heading, paragraph_text), ...].
        """

        sections = []
        heading = ""
        paragraph = []

        def flush():
            body = " ".join(paragraph).strip()
            paragraph.clear()
            if body:
                sections.append((heading, body))

        for line in clean_document_text(text).split("\n"):

            if not line:
                flush()
                continue

            if self._is_heading(line):
                flush()
                heading = line
                continue

            paragraph.append(line)

        flush()

        return sections

    def _sentences(self, paragraph):

        sentences = []

        for sentence in _SENTENCE_SPLIT_PATTERN.split(paragraph):

            sentence = sentence.strip()

            if not sentence:
                continue

            # Very long "sentences" (tables, lists without
            # punctuation) are split on word boundaries.
            if len(sentence) <= self.chunk_size:
                sentences.append(sentence)
                continue

            current = ""

            for word in sentence.split():

                candidate = f"{current} {word}".strip()

                if len(candidate) > self.chunk_size and current:
                    sentences.append(current)
                    current = word
                else:
                    current = candidate

            if current:
                sentences.append(current)

        return sentences

    # ========================================================
    # CHUNKING
    # ========================================================

    def chunk(self, text):

        chunks = []

        # Merge consecutive paragraphs of the same section so short
        # paragraphs are not turned into tiny chunks.
        merged = []

        for heading, body in self._sections(text):

            if merged and merged[-1][0] == heading:
                merged[-1] = (heading, merged[-1][1] + " " + body)
            else:
                merged.append((heading, body))

        for heading, body in merged:

            prefix = f"{heading}: " if heading else ""
            budget = max(self.chunk_size - len(prefix), self.chunk_size // 2)

            current = []
            current_length = 0
            new_since_emit = 0

            for sentence in self._sentences(body):

                extra = len(sentence) + (1 if current else 0)

                if current and current_length + extra > budget:

                    chunks.append(prefix + " ".join(current))

                    keep = (
                        current[-self.overlap_sentences:]
                        if self.overlap_sentences
                        else []
                    )

                    # Never let the overlap alone overflow the budget.
                    while keep and sum(len(s) + 1 for s in keep) + len(sentence) > budget:
                        keep = keep[1:]

                    current = list(keep)
                    current_length = sum(len(s) + 1 for s in current)
                    new_since_emit = 0
                    extra = len(sentence) + (1 if current else 0)

                current.append(sentence)
                current_length += extra
                new_since_emit += 1

            if current and new_since_emit:
                chunks.append(prefix + " ".join(current))

        return chunks
