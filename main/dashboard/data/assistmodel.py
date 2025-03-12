class AssistMixin():
    service_attr = ["_state",]

    def is_changed(self) -> bool:
        """Возвращает True если это новый экземпляр или
           если значения полей данного экземпляра не совпадают
           с значениями полей для экземпляра из БД
           с таким же primary key"""
        result = False
        if not self.pk:
            result = True
        else:
            device_in_db = type(self).objects.get(pk=self.pk)
            equal_fields = (getattr(self, attr) != getattr(device_in_db, attr)
                            for attr in self.__dict__
                            if attr not in self.service_attr)
            if any(equal_fields):
                result = True
        return result

    def get_dict(self, del_attr: tuple = None, rename_attr: tuple = None):
        """Возвращает словарь атрибутов с их значениями
        за исключением атрибутов из списка self.service_attr
        и переданных в параметре del_attr"""
        result = vars(self).copy()
        if isinstance(del_attr, tuple):
            del_attr = (*self.service_attr, *del_attr)
        else:
            del_attr = self.service_attr
        [result.pop(attr, None) for attr in del_attr]
        if isinstance(rename_attr, tuple):
            for old, new in rename_attr:
                result[new] = result[old]
                result.pop(old, None)
        return result

    @classmethod
    def del_empty_args(cls, input_dict: dict):
        """Возвращает словарь без ключей с пустыми значениями"""
        [input_dict.pop(key, None)
         for key in tuple(input_dict.keys()) if input_dict[key] is None]
        return input_dict
