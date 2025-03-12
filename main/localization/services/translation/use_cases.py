from .user_interface import InterfaceTralslation


def get_interface_all_translts(lang: str):
    data = InterfaceTralslation.get_all_translts(lang)
    status = True if data else False
    return {
        "lang": lang,
        "translation": data,
    }, status


def get_all_langs():
    return {"langs": [{inst.code: inst.name}
                      for inst in InterfaceTralslation.get_all_langs()]}
