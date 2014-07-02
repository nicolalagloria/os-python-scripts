#!/usr/bin/python

'''
Filepush: a file publisher to copy Android build file on a httpd directory
Copyright (C) Nicola La Gloria, Kynetics LLC

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
import shutil
import tarfile

def main():
	
	version = "Filepush 1.0 (c) 2014 Nicola La Gloria"

	op = optparse.OptionParser(version=version)

	usage = "filepush.py -s <android-source-root> -d <destionation-dir> -f <file>|-a -c" 

	op.set_usage(usage)
	op.add_option ("-c" , "--compress", action = "store_true", dest = "compress")

	op.add_option ("-a" , "--all", action = "store_true", dest = "copyall")

	op.add_option ("-t" , "--http_root", action = "store", type = "string", dest = "httpd_dir")

	op.add_option ("-d" , "--dest", action = "store", type = "string",  dest = "dest_dir")

	op.add_option ("-f" , "--file", action = "store", type = "string", dest = "file")

	op.add_option ("-p" , "--product", action = "store", type = "string", dest = "product")

	op.add_option ("-s" , "--sources_root", action = "store", type = "string", dest = "sources_root")

	op.set_defaults (compress = False, copyall = False, httpd_dir = "/var/www/", product = "nitrogen6x", 
			sources_root = os.getcwd())

	opt, args = op.parse_args()

	dir = os.path.join(opt.httpd_dir , opt.dest_dir)

	android_out = "out/target/product"
	
	out_dir = os.path.join(opt.sources_root, android_out, opt.product + "/")

	files = []

	if (opt.copyall == True):
		# define fle tuple 
		for name in ["system.img", 
			"uImage", 
			"6x_bootscript", 
			"uramdisk.img",	
			"uramdisk-recovery.img"
			]:
			files.append(name)
	else:
		files.append(opt.file)
	
	copy_files (files, out_dir, dir, opt.compress)
	
def copy_files(files, src_dir, dest_dir, compress):
	
	# create dir if necessary
	if os.path.isdir(dest_dir) is False: 
		print "Creating directory"
		os.mkdir(dest_dir)

	print ("Source directory:"+src_dir)
	print ("Destination directory:"+dest_dir)
	
	for file in files:
		
		try: 
			shutil.copy(src_dir + file, dest_dir)
			print (file + "...copied")
		except IOError as e:
			# if you don't find some files they are in ./boot
			try: 
				shutil.copy(src_dir + "boot/" + file, dest_dir)
				print (file + "...copied")
			except IOError as ee:
				print ("File not Found")
		except Exception as e:
			print ("a general error occurs")

	if compress is True:
		compress_dir(dest_dir, files)	
	return 0

def compress_dir(dest_dir, files):

	os.chdir(dest_dir)
	t = tarfile.open("archive.tar.bz2", 'w:bz2')
	print ("compressing files")
	for file in files:
		t.add(file)
		print (file + "...added to the archive")	
	t.close()
	return 0

if __name__ == '__main__':main()
 
