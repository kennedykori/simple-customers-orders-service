from django.apps import AppConfig


class ShopConfig(AppConfig):
    name = 'apps.shop'

    def ready(self) -> None:
        import apps.shop.signals
