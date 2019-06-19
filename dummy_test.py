#!/usr/bin/env python3
import time
if __name__ == '__main__':

    f_in  = open("./sample.txt", "r")
    f_out = open("backup/demo.log", "w")
    for x in f_in:
      f_out.write(x) 
      time.sleep(0.1)

    f_in.close()
    f_out.close()
