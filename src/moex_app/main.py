import os
import sys
dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.abspath(os.path.join(dir_path, os.pardir))
sys.path.insert(0, parent_dir_path)

from repositories.bond import MoexORM
from services.moex import Bond, BondList, ContextStrategy


def get_info():
    bond = Bond()
    bond_list = BondList()
    client = ContextStrategy(bond_list)
    page = 0
    while True:
        try:
            client.set_strategy(bond_list)
            list_bonds = client.execute_strategy(page=page)
            page += 1
            client.set_strategy(bond)
            bonds = [detail for i in list_bonds
                     if (detail := client.execute_strategy(secid=i))]

            MoexORM.update_data(bonds=bonds)
        except StopIteration:
            break


if __name__ == '__main__':
    get_info()
    # MoexORM.create_tables()
