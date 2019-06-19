#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Simple Bot to report yolo training to Telegram messages.

"""
from repeated_timer import RepeatedTimer
import os
from os import listdir
from os.path import isfile, join
import time
import logging
import telegram
from telegram.error import NetworkError, Unauthorized
from time import sleep
import time
import datetime
import sys
import re
import numpy as np
import matplotlib.pyplot as plt

class Alghoritm(object):
    # Alghoritm initializer neeed a unique id of the session
    def __init__(self, name):

        #Regex to detect ITERATION information line in lof file
        self.line_regex = r"(?P<iter>\d+): (?P<loss>\d+\.\d+), (?P<avg_loss>\d+\.\d+) avg, (?P<rate>\d+\.\d+) rate, (?P<sec>\d+\.\d+) seconds, (?P<n_img>\d+) images"

        self.log_file_found = True # flag to enable log file streaming

        self.bkup_folder = "./backup"   # folder where backup data are stored
        self.log_file_name = 'demo.log' #'yolov3_train.log' 
  
        # TELEGAM BOT INFORMATION
        self.bot = telegram.Bot('584589181:AAEly--lBqcwVFkyncHKn2zNemGOitcKyhc')        
        self.chat_id = -348608801 #97971969 #-385995879#
        
        
        self.log_evry_iter = 50  # iteration to skip before log
        self.check_file_ts = 2   # check esistence of new file every ts seconds
        self.update_id = None

        # Store name of file already in the backup folder, needed for knowing
        # which file is already sended
        self.old_file_list = self.fileInFolder()        
        now = datetime.datetime.now()
        message = "*=======================+\n"
        message += "|    ____             \n"
        message += "|    |DD|______T_     \n" 
        message += "|    |___|________.|<  \n"
        message += "|     @-@-@-oo\\      \n"
        message += "|=======================+\n"
        message += "|===>            TRAIN\n"
        message +=  now.strftime("| Day:  %d-%m-%Y\n")
        message +=  now.strftime("| Time: %H:%M:%S\n")
        message += "| Name: " + name + "\n"
        message += "*=======================+\n"
        try:
            self.bot.sendMessage(self.chat_id, message)
            self.bot_log_enabled = True
        except:
            logging.info("WARNING: Running with no timer")
            self.bot_log_enabled = False

        if self.log_file_found and self.bot_log_enabled: 
          # If we have a bot to comunicate with and log file enabled

          log_file_path = self.bkup_folder +"/"+ self.log_file_name
          # Wait generation of log file and open it
          while not os.path.isfile(log_file_path):
              try:           
                  logging.warn("Logging file not found waiting: " + log_file_path)
                  self.bot.sendMessage(self.chat_id, "!!! Can not find log file !!!\n")
                  sleep(4)
              except KeyboardInterrupt:
                  logging.info("ctrl C caught terminating")
                  sys.exit(1)
          self.old_file_list.append(self.log_file_name)
          self.log_file = open(log_file_path,'r+')
        
        # Run the alghoritm
        self.run()

    # Get the file contained in self.bkup_folder
    def fileInFolder(self):
        return [f for f in listdir(self.bkup_folder) if isfile(join(self.bkup_folder, f))]

    # Check if there are new file in the self.bkup_folder    
    def checkNewFiles(self):
        actual_files = self.fileInFolder()
        new_files = []
        for f in actual_files:
            if f not in self.old_file_list:
                new_files.append(f)  
        return new_files

    # Periodic timer callback to check if new files are created
    def new_file_timer_callback(self):
        logging.info("check if new files callback")
        #logging.info("Already sended file: ")
        #for f in self.old_file_list:
        #    logging.info("\t|--> " + f)
    
        try:
          new_files = self.checkNewFiles() 
          if new_files:   
            # Try to publish the file!
            logging.info("New found file: ")
            for f in new_files:
                logging.info("\t|--> " + f)
            
            for f_name in new_files:
                self.old_file_list.append(f_name)
                #TODO: check if FILE IS NOT EMPTY!!! Error when it is empty
                f_path = self.bkup_folder + "/" + f_name
                logging.info("Sending: " + f_path)
                
                now     = datetime.datetime.now()
                message = "|----> NEW FILE\n"
                message +=  now.strftime("|  |--> Day:  %d-%m-%Y\n")
                message +=  now.strftime("|  |--> Time: %H:%M:%S\n")
                message += "|  '--> File: " + f_name + "\n"             
                self.bot.sendMessage(self.chat_id, message)
                
                sleep(0.5)
                # TODO: max file size is limited only at 50MB, better to run a bash command to store on https://transfer.sh/ 
                # Example idea:
                #       -> run with nohup the following
                #       -> curl --upload-file ./hello.txt https://transfer.sh/hello.txt > ./backup/FILEname.txt
                #       -> when the process is completet upload this small file or put in a list the file addres
                self.bot.sendDocument(self.chat_id, document=open(f_path, 'rb'), timeout=10000)
                
                logging.info("New old file list: ")
                for f in self.old_file_list:
                    logging.info("\t|--> " + f)
              
        except:
            logging.info("CANNOT PUBLISH FILE!")   

    # When the user send a message to the bot it is processed here!
    def echo(self):
        """Echo the message the user sent."""
        global update_id
        # Request updates after the last update_id
        for update in self.bot.get_updates(offset=self.update_id, timeout=10):
            logging.info('Get an update')
            self.update_id = update.update_id + 1

            if update.message:
                if update.message.text == "/id":
                    back_message = "chat ID is: " + str(update.message.chat.id)
                else:
                    back_message = "I am on"
                update.message.reply_text(back_message )


    # Runner 
    def run(self):
        # get the first pending update_id, this is so we can skip over it in case
        # we get an "Unauthorized" exception.
        try:
            self.update_id = self.bot.get_updates()[0].update_id        
        except IndexError:
            self.update_id = None
 
        # Create repeated timer to check for new file
        if self.bot_log_enabled:
            new_file_timer = RepeatedTimer(self.check_file_ts, self.new_file_timer_callback )
            new_file_timer.start()
          

        line_count = 0 
        info_ready = False
        info_msg=""
        loss_list=[]
        # Loop checking for user message and new useful log line
        while True:
            try:
                if self.log_file_found and self.bot_log_enabled:
                    logging.info("Check log")
                    message=""
                    figure_name=""
                    while len(message) < 100*40:
                        where = self.log_file.tell()
                        line  = self.log_file.readline()
                        if line:
                            if line_count < 35:
                                #TODO: check if line == "Done!" for support network with different layers number
                                info_msg    += line
                                line_count +=1
                                if line_count>34:
                                    try:
                                        self.bot.sendMessage(self.chat_id, info_msg)
                                    except:
                                        logging.info("Failed to send INFO message!")  
                            else:
                                # Check if the row match the ITER lane
                                data_match = re.findall(self.line_regex, line)

                                if data_match:
                                    # Lane report ITER result
                                    data_match = data_match[0]
                                    iter_n = int(data_match[0])
                                    loss_v = float(data_match[1])
                                    loss_list.append(loss_v)
                                    logging.info("ITERATION NUMBER: " + str(iter_n))

                                    if iter_n == 1 or (iter_n % self.log_evry_iter)==0:
                                        loss_np = np.asarray(loss_list, dtype=np.float32)

                                        # Create training loss graph
                                        figure_name = self.bkup_folder + "/iter"+ data_match[0] + ".png"
                                        plt.clf()
                                        plt.plot(loss_np, 'o-')
                                        plt.title('Iteration: ' +  data_match[0])
                                        plt.ylabel('Loss')
                                        plt.xlabel('Iteration')
                                        #plt.show()
                                        plt.savefig(figure_name, bbox_inches='tight')
                                        message += "|----> ITER "  + data_match[0] + "\n"
                                        message += "|  |--> loss " + data_match[1] + "\n"
                                        message += "|  |--> avg  " + data_match[2] + "\n"
                                        message += "|  |--> sec  " + data_match[4] + "\n"
                                        message += "|  '--> img  " + data_match[5] + "\n"
                                 
                        else:
                            self.log_file.seek(where)     
                            if len(message)>0:
                                logging.info("Sending ITERATION message!")
                                try:
                                    self.bot.sendMessage(self.chat_id, message)  
                                except:
                                    logging.info("Iteratino message skipped can not send!")   
                            break
                    
                
                    time.sleep(1)
                    logging.info("check file in backup folder")
                    try:
                        self.echo()
                    except NetworkError:
                        logging.info("NETWORK ERROR")
                        sleep(1)
                    except Unauthorized:
                        # The user has removed or blocked the bot.
                        logging.info("UNAUTHORIZED")
                        update_id += 1
            except KeyboardInterrupt:
                # TODO: maybe add a big could be needed to ensure all file are loaded
                logging.info("ctrl C caught terminating")
                break
        new_file_timer.stop()
        self.log_file.close()

  

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO) #level=logging.DEBUG
    if len(sys.argv)==2:
        logging.info("Init alghoritm with name: " + sys.argv[1])        
        Alghoritm(sys.argv[1])
    else:
        print("Error: expected only 1 input argument (i.e. the name of the session)")

    
      

