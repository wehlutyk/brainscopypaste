# usage: python parsexml.py < infile 
import sys
import re
import os
import optparse
import time

TOTALSIZE = 0
CURSIZE = 0
STARTTIME = 0


#####################################
def trimtoalpha(string):
    string = re.sub('&amp;','&', string) # change &amp to &
    string = re.sub('&lt','<', string) # change &lt; to <
    string = re.sub('&gt','>', string)  # change &gt; to >
    string = re.sub('<[^<>]*>', ' ', string) # drop anything in <>
    string = re.sub('&#\d+;','', string) # change &#[digits]; to space
    string = re.sub('&quot;',' ', string) # change &quot; to space
    string = re.sub('http://[^ ]+ ', " ", string) # drop urls
    string = re.sub('-', "", string) # drop non-alphanumeric characters
    string = re.sub('[^0-9a-zA-Z ]', "", string) # drop non-alphanumeric characters
    string = re.sub('\s+', " ", string) # condense spaces
    return string

#####################################
def parsexmlfiles(filepath):
    global TOTALSIZE, CURSIZE
    # if directory, parse recursively
    if os.path.isdir(filepath):
        print 'Exploring directory ' + filepath
        files = os.listdir(filepath)
        for file in files:
            parsexmlfiles(os.path.join(filepath, file))
    elif filepath.endswith('.xml'):
        print 'Parsing xml ' + filepath
        newfilepath = parsefile(filepath)
#        print 'Stripping file with system command ' + filepath
        # use unix to parse file, it's faster
#        cmd = "scripts/stripsingle.sh " + newfilepath
#        print cmd
#        os.system(cmd)
    else:
        print 'Ignoring file ' + filepath
    if not os.path.isdir(filepath) and not TOTALSIZE == 0:
        CURSIZE = CURSIZE + os.path.getsize(filepath)
        pctdone = float(CURSIZE) / float(TOTALSIZE);
        curtime = time.time()
        etime = curtime - STARTTIME
        rtime = etime/(pctdone) - etime          
        print str(CURSIZE) + ' out of ' + str(TOTALSIZE) + ' kilobytes processed;',
        print "%3.2f%% done," %(100*pctdone),
        print sectostring(etime) + " elapsed,",
        print sectostring(rtime) + " remaining."
        
#####################################
def parsefile(filepath):
    # read in file
    fin = open(filepath,'r')
    lines = fin.readlines()
    # open output file with '.txt'
    newfilepath = filepath[0:-4] + '.txt'
    fout = open(newfilepath, 'w')
    inblock = False
    docidx = 0;
    for line in lines:
        line = line.strip()
        if line.startswith("<description>"):
            fout.write(str(docidx) + " " + trimtoalpha(line) + ' ') # print line except for '<description>' start
            inblock = True
            docidx += 1
        elif inblock:
            fout.write(trimtoalpha(line) + ' ')            
            if line.find("</description>") >= 0:
                inblock = False
                fout.write("\n")
    fout.close()
    return newfilepath

#####################################
def stripfiles(filepath):
    global TOTALSIZE, CURSIZE
    # if directory, parse recursively
    if os.path.isdir(filepath):
        print 'Exploring directory ' + filepath
        files = os.listdir(filepath)
        for file in files:
            stripfiles(os.path.join(filepath, file))
    elif filepath.endswith('.parsed'):
        print 'Stripping file ' + filepath
        stripfile(filepath)
        # use unix to parse file, it's faster
 #       cmd = "scripts/stripsingle.sh " + filepath
 #       print cmd
 #       os.system(cmd)
    else:
        print 'Ignoring file ' + filepath
    if not os.path.isdir(filepath) and not TOTALSIZE == 0:
        CURSIZE = CURSIZE + os.path.getsize(filepath)
        pctdone = float(CURSIZE) / float(TOTALSIZE);
        curtime = time.time()
        etime = curtime - STARTTIME
        rtime = etime/(pctdone) - etime          
        print str(CURSIZE) + ' out of ' + str(TOTALSIZE) + ' kilobytes processed;',
        print "%3.2f%% done," %(100*pctdone),
        print sectostring(etime) + " elapsed,",
        print sectostring(rtime) + " remaining."
        
#####################################
def stripfile(filepath):
    # read in file
    fin = open(filepath,'r')
    lines = fin.readlines()
    # open output file with '.parsed'
    newfilepath = filepath[0:-7] + '.txt'
    fout = open(newfilepath, 'w')
    docidx = 0
    for line in lines:
        line = line.strip()
        fout.write(str(docidx) + " " + trimtoalpha(line) + '\n') # print line except for '<description>' start
        docidx += 1
    fout.close()
    return newfilepath

#####################################
def getDirectorySize(directory):
    dir_size = 0
    for (path, dirs, files) in os.walk(directory):
        for file in files:
            filename = os.path.join(path, file)
            dir_size += os.path.getsize(filename)
    return dir_size


#####################################
def sectostring(seconds):
    minutes = seconds / 60.0
    hours = minutes / 60.0
    days = hours / 24.0
    timestr = "%2.0f" %(seconds) + ' sec'
    if days > 1:
        timestr = "%2.1f" %(days) + ' hr'
    elif hours > 1:
        timestr = "%2.1f" %(hours) + ' hr'
    elif minutes > 1:
        timestr = "%2.1f" %(minutes) + ' min'
    return timestr

#####################################
if __name__ == '__main__':
    usage = "usage: %prog dirpath"
    p = optparse.OptionParser(usage=usage)
    p.add_option("-s", "--striponly", action="store_true", default=False, help="Only strip parsed files, no need to parse xml")
    
    (opts, args) = p.parse_args()
    if not len(args) == 1:
        print usage
        p.error('Please specify a directory to parse.')
#    if not os.path.isdir(args[0]):
#        print usage
#        p.error('Please specify a directory to parse.')

    print('Getting total directory size...')
    TOTALSIZE = getDirectorySize(args[0])
    print('Total data amount is ' + str(TOTALSIZE/1000) + ' kilobytes.')
    STARTTIME = time.time()
    if opts.striponly:
        stripfiles(args[0])
    else:
        parsexmlfiles(args[0])
#####################################
