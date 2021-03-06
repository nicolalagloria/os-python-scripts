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
from time import sleep


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

    op.add_option("-s", "--disk", action="store", dest="disk")

    op.add_option("-e", "--erase_dos", action="store_true", dest="erasedos")

    op.add_option("-p", "--apps_local_dir", action="store", type="string", dest="apps_local_dir")

    op.add_option("-q", "--apps_device_dir", action="store", type="string", dest="apps_device_dir")

    op.add_option("-i", "--img_dir", action="store", type="string", dest="img_dir")

    op.add_option("-m", "--mount_dir", action="store", type="string", dest="mount_dir")

    op.add_option("-f", "--filesystem", action="store", type="string", dest="filesystem")

    op.set_defaults(disk="/dev/null", erasedos=True, img_dir=os.getcwd(), filesystem="ext4",
                    apps_local_dir='{0}/apps'.format(os.getcwd()), apps_device_dir="app",
                    mount_dir=tempfile.mkdtemp("-andr_part"))

    opt, args = op.parse_args()

    if os.geteuid() != 0:
        exit("You need to have root privileges")

    partition_disk(opt.disk)

    partitions = {
        "BOOT": ["1", ["6x_bootscript", "uImage", "uramdisk.img"]],
        "RECOVERY": ["2", ["6x_bootscript", "uImage", "uramdisk-recovery.img"]],
        "DATA": ["4", []],
        "CACHE": ["6", []],
        "VENDOR": ["7", []],
        "MISC": ["8", []],
    }

    format_partitions(opt.disk, partitions, opt.filesystem)

    mount_partitions(opt.disk, opt.mount_dir, partitions, opt.filesystem)

    write_disk(opt.disk, opt.img_dir, opt.apps_local_dir, opt.apps_device_dir, partitions)

    umount_partitions(opt.mount_dir, partitions)

    return 0


def partition_disk(disk):
    # todo: enable different sizes of disks. Now only 4 GB card are supported

    # erase partition table

    print "Erasing Partition Table"
    erase_cmd = ["dd", "if=/dev/zero", "of=" + disk, "bs=512", "count=4000"]
    erase = subprocess.Popen(erase_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # out = erase.stdout.read()
    os.waitpid(erase.pid, 0)

    # Partition disk

    print "Partitioning Disk"

    cmd = ["sfdisk", "--force", "-L", "-uM", disk]

    # It's relevant that NO SPACES need to be present in the cmd string string of sfdisk

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
    pobj = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = pobj.communicate(cmd_string)
    print err
    print out
    # TODO: IO Error handling   

    sync_disk()

    print "Done"

    return 0


def mount_partitions(disk, mnt_dir, partitions, fs):
    # Parent directory --parent of mkdir is not supported in pythin 2.x
    if not os.path.exists(mnt_dir):
        os.mkdir(mnt_dir)

    for pname in partitions:
        mypath = os.path.join(mnt_dir, pname)
        if not os.path.exists(mypath):
            os.mkdir(mypath)
        # Append to the partition structure the destination path for such partition
        partitions.get(pname).append(mypath)

    print "Mount points created in " + mypath

    for pname in partitions:
        mypath = os.path.join(mnt_dir, pname)
        if not os.path.ismount(mypath):
            mount_cmd = ["mount", "-t" + fs, disk + partitions.get(pname)[0], mypath]
            p = subprocess.Popen(mount_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print "Mounting " + mypath
            os.waitpid(p.pid, 0)
        else:
            continue
    print "DONE"

    return 0


def umount_partitions(mnt_dir, partitions):
    print "Unmouting partitions"
    for pname in partitions:
        mypath = os.path.join(mnt_dir, pname)
        if os.path.ismount(mypath):
            umount_cmd = ["umount", mypath]
            p = subprocess.Popen(umount_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            sleep(2)
            while p.poll() is None:
                print p.poll()
                p.wait()
        shutil.rmtree(mypath)
    # remove the parent
    os.rmdir(mnt_dir)
    print "DONE"

    return 0


def write_disk(disk, source_dir, apps_local_dir, apps_device_dir, partitions):
    # Return files the in the apps dir
    try:
        apps = os.listdir(apps_local_dir)
    except OSError:
        apps = []

    # TODO: exit and unmount all partitions if an error occurs when copying files
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
                    os.rename(partitions.get(pname)[2] + "/" + file, partitions.get(pname)[2] + "/uramdisk.img")
        elif (pname == "DATA") and apps:        # Are there apps to install?
            print "copying files in " + pname
            if not os.path.isdir(partitions.get(pname)[2] + "/" + apps_device_dir):
                os.mkdir(partitions.get(pname)[2] + "/", apps_device_dir)
            for app in apps:
                shutil.copy(apps_local_dir + "/" + app, partitions.get(pname)[2] + "/app")
        else:
            continue

    sync_disk()

    # Write System

    print "Writing System image"
    write_system_cmd = ["dd", "if=" + source_dir + "/system.img", "of=" + disk + "5"]
    write = subprocess.Popen(write_system_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.waitpid(write.pid, 0)

    label_cmd = ["e2label", disk + "5", "SYSTEM"]
    label = subprocess.Popen(label_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.waitpid(label.pid, 0)

    print "DONE"

    sync_disk

    return 0


def sync_disk():
    print "syncing disk"
    sync = subprocess.Popen("sync", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    os.waitpid(sync.pid, 0)
    return 0


def format_partitions(disk, partitions, fs):
    for pname in partitions:
        format_cmd = ["mkfs." + fs, "-L" + pname, disk + partitions.get(pname)[0]]
        print fs + ":" + "formatting " + disk + partitions.get(pname)[0] + " with label " + pname
        p = subprocess.Popen(format_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.waitpid(p.pid, 0)

    sync_disk()
    print "DONE"

    return 0


if __name__ == '__main__': main()

