from unittest.mock import Mock, patch

from ij_open_data.scrap_open_data_cnam_ij import get_links_from_main_page


@patch("ij_open_data.scrap_open_data_cnam_ij.requests.get")
def test_get_links_from_main_page(mock_get):
    """Test simple de get_links_from_main_page avec des liens mockés."""

    # HTML simple avec quelques liens
    html_content = """
    <html>
        <a href="/etudes-et-donnees/ij-2023">Données IJ 2023</a>
        <a href="/autre-page">Autre page</a>
        <a href="/etudes-et-donnees/stats-ij">Stats IJ</a>
    </html>
    """

    # Mock de la réponse HTTP
    mock_response = Mock()
    mock_response.text = html_content
    mock_get.return_value = mock_response

    # Test
    base_url = "https://example.com"
    result = get_links_from_main_page(base_url)

    # Vérifications
    assert len(result) == 2
    assert "https://example.com/etudes-et-donnees/ij-2023" in result
    assert "https://example.com/etudes-et-donnees/stats-ij" in result
