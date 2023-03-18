try:
    import subprocess
    import glob
    import os
    import sys
    import time

    for config_file in glob.glob(os.path.join(os.getcwd(), "cfg", "*.csv")):
        current_time = time.strftime("%H:%M:%S", time.localtime())
        try:
            with open(os.path.join(".", "last_run.log"), 'w') as log:
                #Write basic log info
                log.write('_' * 100 + '\n')
                log.write(f"Logfile created at {current_time}" + '\n')
                log.write(f"Experiment path: {config_file}" + '\n')
                log.write('_' * 100 + '\n')

                #Run main
                sp = subprocess.Popen(["python", "./src/main.py", config_file], stdin=None,
                                    stdout=subprocess.PIPE, stderr=log)
                response = sp.communicate()[0].strip()

                #Remove all the files from temp dir
                try:
                    tempdirfiles = os.listdir(os.path.join(".", "data", "temp"))
                    for f in tempdirfiles:
                        try:
                            os.remove(os.path.join(".", "data", "temp", f))
                        except Exception as error:
                            log.write(f"WARNING: unable to remove temporary garbage {f}!" + '\n')
                            log.write(str(error))
                            log.write('\n')
                except Exception as error:
                    log.write("WARNING: temporary garbage cleaning failed! (temp doesn't exist?)" + '\n')
                    log.write(str(error))
                    log.write('\n')

            #Analyze main print from pipe
            if response == b"True":
                print("Program exit...")
                break
            elif response == b"False":
                print(f"Experiment {config_file} was completed")
            else:
                raise Exception
        except:
            print(f"ERROR: experiment {config_file} was terminated with incorrect response!")
            break

except Exception as error:
    print("ERROR: iterator stopped its work due to unexpected error!")
    print(error)