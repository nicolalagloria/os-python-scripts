#!/usr/bin/python

'''
pymake:

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
import py_compile
import optparse
import os
def main():
    
    version = "pymake 1.0 (c) 2014 Nicola La Gloria"

    op = optparse.OptionParser(version=version)

    usage = """This is the usage """
        
    op.set_usage(usage)
    
    op.add_option ("-f" , "--file", action = "store", dest = "filename")
    
    opt, args = op.parse_args()
        
    compile_file(opt.filename)
    

def compile_file(filename):
    
    print "Compile module"

    py_compile.compile(filename)
    
    exe_name = filename.split(".")[0]
    
    os.rename(exe_name + ".pyc",exe_name)    
        
    os.chmod(exe_name,755)
    
    print "done."
    return 0
if __name__ == '__main__':main()
