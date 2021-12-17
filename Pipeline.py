from LTE_modules import *
import sys
print_to_file = False
if __name__ == '__main__':
    if print_to_file:
        sys.stdout = open("output_file.txt", "w")
    ue = UE()
    enb = eNb()
    mme = MME()
    hss = HSS()
    sgw = SGW()
    pgw = PGW()

    ue.attach()

    sleep(2)
    ue.detach()

