from ij_open_data.utils import hello


def test_hello():
    assert hello() == "\n\n" "################\n" "# Hello World! #\n" "################\n"
