# MHSB-10: UrunRepository (minimum iskelet)
class UrunRepository:
    def get(self, urun_id):
        raise NotImplementedError

    def create(self, data):
        raise NotImplementedError

    def update(self, urun_id, data):
        raise NotImplementedError

    def delete(self, urun_id):
        raise NotImplementedError
