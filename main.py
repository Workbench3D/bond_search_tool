from database import MoexORM
from routers import MoexBond


def get_info():
    MoexORM.create_tables()
    moex = MoexBond()
    list_bonds = moex.generator_bonds()
    for i in range(moex.num_page):
        try:
            bonds = [detail for i in next(list_bonds)
                     if (detail := moex.get_detail_bond(secid=i))]
            MoexORM.insert_data(bonds=bonds)
        except StopIteration:
            break


def get_revenue_bonds():
    moex = MoexBond()
    list_secids = MoexORM.select_secid()

    final = [moex.calc_bond(secid=i.get('secid')) for i in list_secids]

    return final


if __name__ == '__main__':
    get_info()
    # get_revenue_bonds()
