from project.items import Product
from web_poet import Returns, WebPage, handle_urls


@handle_urls("www.e-u-z.de")
class EUZDeProductPage(WebPage, Returns[Product]):
    pass
