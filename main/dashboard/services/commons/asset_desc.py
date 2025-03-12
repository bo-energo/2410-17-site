from dataclasses import dataclass
from main.settings import MEDIA_URL


@dataclass
class AssetDesc:
    """Короткое описание актива (оборудования)"""
    id: int = None
    guid: str = ""
    name: str = ""
    type_name: str = ""
    type_code: str = ""
    model: str = ""
    subst_id: int = None
    subst_name: str = ""
    image: str = None
    scheme_image: str = None
    subst_scheme_image: str = None
    on_scheme_x: int = None
    on_scheme_y: int = None

    def get_image_url(self):
        if self.image:
            return self.image
        else:
            return f"{MEDIA_URL}default_asset_images/{self.type_code}.png"

    def get_scheme_image_url(self):
        if self.scheme_image:
            return self.scheme_image
        else:
            return None

    def get_subst_scheme_image_url(self):
        return self.subst_scheme_image
