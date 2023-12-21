from datetime import datetime
from database import MoexORM
from routers import BondList, Bond, MoexClient


def get_info():
    # MoexORM.create_tables()
    bond_strategy = Bond()
    bond_list_strategy = BondList()
    page = 0
    while True:
        try:
            list_bonds = next(
                bond_list_strategy.generator_bonds(page=page))
            page += 1
            bonds = [detail for i in list_bonds
                     if (detail := bond_strategy.get_detail_bond(i))]

            # MoexORM.insert_data(bonds=bonds)
        except StopIteration:
            break


# def get_revenue_bonds():
#     moex = MoexBond()
#     list_secids = MoexORM.select_secid()

#     final = [moex.calc_bond(secid=i.get('secid')) for i in list_secids]

#     return final


if __name__ == '__main__':
    get_info()
    # get_revenue_bonds()
