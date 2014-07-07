#!/usr/bin/python
'''
mksdcard: a sdcard programming tool for Android build

Copyright(C)2014, Nicola La Gloria, Kynetics LLC

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

'''

import optparse
import os
import subprocess
import tempfile
import shutil 

def main():
    
    version = "mksdcard 1.0 (c) 2014 Nicola La Gloria"

    op = optparse.OptionParser(version=version)

    usage = """mksdcard --disk /dev/sdb --apps_dir=/your/apps/dir -i /your/android/build/files \n
    
    The standard Android partitions are:
    
        partition 1 = BOOT
        partition 2 = RECOVER
        partition 3 = extended
        partition 4 = DATA
        partition 5 = SYSTEM
        partition 6 = CACHE
        partition 7 = VENDOR
        partition 8 = MISC
        
    The minimum required build files are:
    1) Bootscript
    2) uImage
    3) uramdisk.img
    4) uramdisk-recovery.img
    5) system.img
    6) your apps (system or user apps)
    """ 

    op.set_usage(usage)
    
    op.add_option ("-s" , "--disk", action = "store", dest = "disk")

    op.add_option ("-e" , "--erase_dos", action = "store_true", dest = "erasedos")

    op.add_option ("-p" , "--apps_dir", action = "store", type = "string", dest = "apps_dir")

    op.add_option ("-i" , "--img_dir", action = "store", type = "string",  dest = "img_dir")

    op.add_option ("-m" , "--mount_dir", action = "store", type = "string",  dest = "mount_dir")

    op.add_option ("-f" , "--filesystem", action = "store", type = "string", dest = "filesystem")

    op.set_defaults (disk = "/dev/null", erasedos = True, img_dir = os.getcwd(), filesystem = "ext4", apps_dir = os.getcwd()+"/apps", mount_dir = tempfile.mkdtemp("-andr_part-"))

    opt, args = op.parse_args()

    if os.geteuid() != 0:
        exit("You need to have root privileges")
        
    partition_disk(opt.disk)

    partitions = {
            "BOOT":["1", ["6x_bootscript", "uImage", "uramdisk.img"]],
            "RECOVERY":["2",["6x_bootscript", "uImage", "uramdisk-recovery.img"]],
            "DATA":["4",[]],
            "CACHE":["6",[]],
            "VENDOR":["7",[]],
            "MISC":["8",[]],
            }
            
    format_partitions(opt.disk,partitions,opt.filesystem)
    
    mount_partitions(opt.disk, opt.mount_dir, partitions,opt.filesystem)
    
    write_disk(opt.disk, opt.mount_dir, opt.img_dir, opt.apps_dir, partitions)
    
    unmount_partitions(opt.disk, opt.mount_dir, partitions)
    
    return 0

def partition_disk(disk):
    
    # todo: enable different sizes of disks. Now only 4 GB card are supported

    # erase partition table
    
    print "Erasing Partition Table"
    erase_cmd = ["dd", "if=/dev/zero","of=" + disk, "bs=512","count=4000"]
    erase =  subprocess.Popen(erase_cmd, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    out= erase.stdout.read()
    os.waitpid(erase.pid,0)
    
    # Partition disk
    
    print "Partitioning Disk"
    
    
    cmd = ["sfdisk", "--force", "-L", "-uM",disk] 
    
   # It's relevant that NO SPACES neeed to be present in the cmd string string of sfdisk 

    cmd_string = """
,20,83,*
,20,83
,2048,E
,,83
,512,83
,512,83
,10,83
,10,83
"""
    pobj = subprocess.Popen(cmd, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    out,err = pobj.communicate(cmd_string)
    print err
    print out
    # TODO: IO Error handling   
    
    sync_disk()

    print "Done"

    return 0


def mount_partitions(disk,tmp_dir,partitions,fs):
    
    for pname in partitions:
        os.mkdir(tmp_dir+pname)
        # Append to the partition structure the destination path for this partition
        partitions.get(pname).append(tmp_dir+pname)
        
    print "Mount points created in "+tmp_dir
    
    for pname in partitions:
        if os.path.ismount(tmp_dir + pname)== False:        
            mount_cmd = ["mount", "-t"+fs,disk+partitions.get(pname)[0],tmp_dir+pname]
            p = subprocess.Popen(mount_cmd, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            print "Mounting "+tmp_dir+pname
            os.waitpid(p.pid,0)
        else:
            continue
    print "DONE"
    
    return 0

def unmount_partitions(disk,tmp_dir,partitions):
    
    print "Unmouting partitions"
    for pname in partitions:
        if os.path.ismount(tmp_dir+pname) == True:
            umount_cmd = ["umount", tmp_dir+pname]
            p = subprocess.Popen(umount_cmd, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
            os.waitpid(p.pid,0)
            os.rmdir(tmp_dir+pname)
    print "DONE"
    
    return 0

        
def write_disk(disk,dest_dir, source_dir, apps_dir, partitions):


    # Return files the in the apps dir
    apps = os.listdir(apps_dir)
    
    for pname in partitions:
        if pname == "BOOT":
            print "copying files in " + pname
            for file in partitions.get(pname)[1]:
                shutil.copy(source_dir + "/" + file, partitions.get(pname)[2])
        elif pname == "RECOVERY":
            print "copying files in " + pname            
            for file in partitions.get(pname)[1]:
                shutil.copy(source_dir + "/" + file, partitions.get(pname)[2])
                if file == "uramdisk-recovery.img":
                    os.rename(partitions.get(pname)[2]+ "/" +file, partitions.get(pname)[2]+ "/uramdisk.img")
        elif pname == "DATA":
            print "copying files in " + pname
            if os.path.isdir(partitions.get(pname)[2]+"/app") == False:
                os.mkdir(partitions.get(pname)[2]+"/app")
            for app in apps:
                shutil.copy(apps_dir + "/" + app, partitions.get(pname)[2]+"/app") 
        else:
            continue
    
    sync_disk()
    
    # Write System
    
    print "Writing System image"
    write_system_cmd = ["dd", "if=" + source_dir + "/system.img","of=" + disk + "5"]
    write =  subprocess.Popen(write_system_cmd, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    os.waitpid(write.pid,0)
    
    label_cmd = ["e2label", disk + "5", "SYSTEM"]
    label =  subprocess.Popen(label_cmd, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    os.waitpid(label.pid,0)
    
    print "DONE"
    
    sync_disk
    
    return 0

def sync_disk():
    print "syncing disk"
    sync = subprocess.Popen("sync", stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
    os.waitpid(sync.pid,0)
    return 0

def format_partitions(disk,partitions,fs):
    
    for pname in partitions:
        format_cmd = ["mkfs."+fs,"-L" + pname, disk + partitions.get(pname)[0]]
        print fs+":"+"formatting "+disk+partitions.get(pname)[0]+" with label "+ pname
        p = subprocess.Popen(format_cmd, stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
        os.waitpid(p.pid,0)
    
    sync_disk()
    print "DONE"

    return 0

if __name__ == '__main__':main()

