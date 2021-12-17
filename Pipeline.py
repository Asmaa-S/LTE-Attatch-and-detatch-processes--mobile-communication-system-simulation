from LTE_modules import *

if __name__ == '__main__':
    ue = UE()
    enb = eNb()
    mme = MME()
    hss = HSS()
    sgw = SGW()
    pgw = PGW()

    ue.attach()

    sleep(10)
    ue.detach()
