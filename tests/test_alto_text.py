from bnf_p0.alto import alto_to_text, decode_alto

# Gallica déclare ISO-8859-1 mais sert de l'UTF-8 : la déclaration ment.
ALTO = (
    '<?xml version="1.0" encoding="ISO-8859-1" standalone="no"?>'
    '<alto xmlns="http://www.loc.gov/standards/alto/ns-v3#"><Layout><Page><PrintSpace>'
    '<TextBlock><TextLine><String CONTENT="COMÉDIE"/><String CONTENT="française"/></TextLine>'
    '<TextLine><String CONTENT="général"/></TextLine></TextBlock>'
    '<TextBlock><TextLine><String CONTENT="d\'Ériphile"/></TextLine></TextBlock>'
    '</PrintSpace></Page></Layout></alto>'
).encode("utf-8")


def test_lying_encoding_declaration_is_corrected():
    assert 'encoding="UTF-8"' in decode_alto(ALTO)


def test_accents_survive_the_round_trip():
    text = alto_to_text(ALTO)
    assert "COMÉDIE" in text
    assert "général" in text
    assert "Ã" not in text


def test_reading_order_lines_then_blocks():
    assert alto_to_text(ALTO) == "COMÉDIE française\ngénéral\n\nd'Ériphile"


def test_utf8_declaration_is_left_alone():
    alto = ALTO.replace(b'ISO-8859-1', b'UTF-8')
    assert "COMÉDIE" in alto_to_text(alto)
