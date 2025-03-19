class SgGuide:
    def __init__(self, code, name, mms_logical_node, mms_data_object, mms_fc):
        self._code = code
        self._name = name
        self._mms_logical_node = mms_logical_node
        self._mms_data_object = mms_data_object
        self._mms_fc = mms_fc

    def get_mms_object_node(self):
        if self._mms_data_object:
            return self._mms_data_object.split(".", 1)[0]
        else:
            return None

    def get_mms_object_node_value(self):
        if self._mms_data_object is None:
            return None
        split_mms_object = self._mms_data_object.split(".", 1)
        if len(split_mms_object) > 1:
            return split_mms_object[-1]
        else:
            return None

    def get_formatted_for_mms_config(self):
        return {
            "signal": self._code,
            "code": self.get_mms_object_node(),
            "name": self._name,
            "value_node": self.get_mms_object_node_value(),
            "LN": self._mms_logical_node,
            "FC": self._mms_fc
        }
