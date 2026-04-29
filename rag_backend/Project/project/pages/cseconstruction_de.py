from project.items import Product
from web_poet import Returns, WebPage, handle_urls


@handle_urls("www.cseconstruction.de")
class CSEConstructionDeProductPage(WebPage, Returns[Product]):
    pass
