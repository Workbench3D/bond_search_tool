from database import MoexORM
from routers import BondList, Bond, ContextStrategy


def get_info():
    # MoexORM.create_tables()
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


# def get_revenue_bonds():
#     moex = MoexBond()
#     list_secids = MoexORM.select_secid()

#     final = [moex.calc_bond(secid=i.get('secid')) for i in list_secids]

#     return final


if __name__ == '__main__':
    get_info()
    # get_revenue_bonds()
