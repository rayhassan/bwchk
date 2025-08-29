#!/usr/bin/env python

"""   bwchk.py - runs iperf command iteratively between a series of ips/hosts 

    Copyright (C) <2014>  <ray@nutanix.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>."""

import multiprocessing
import subprocess
import argparse
import sys


def run_iperf(iperf_cmd, cvm_ip, verbose):

    """
        Tack on the ssh login details and launch command via popen.
        Note: we rely on passwordless ssh.
    """

    ssh_cmd = ["/usr/bin/ssh", "-l", "nutanix", cvm_ip] 
    cmd = ssh_cmd + iperf_cmd

    if verbose:
        print ("cmd: %s" % cmd)
    try:
        process = subprocess.Popen(cmd,
                              bufsize=1,
                              stderr=subprocess.PIPE,
                              stdout=subprocess.PIPE,
                              shell=False)
        output, error = process.communicate()
    except OSError as e:
        e.action = "launching subprocess via popen"
        text = "Error'd at %s: %s" % (e.action, e)
        sys.exit(text)

    #if process.returncode == 0:
    #    retcode = process.returncode
    print ("%s" % output)
    sys.stdout.flush()
    return 

def configure_parser():

    """ Look to change this to use argparse rather than optparse"""

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('-v', '--verbose', dest='verbose',
                        help='show output from individual commands',
                        action='store_true')
    arg_parser.add_argument('-i', '--cvmips',
                        help='comma separated list of CVM host/IP addresses',
                        required=True)
    return arg_parser


def main():

    parser = configure_parser()
    (opts, args) = parser.parse_args()

    cvm_list=opts.cvmips.split(",")
    if opts.verbose:
        print ("cvm_list: %s" % cvm_list)
    for cvm_ip in cvm_list:
        server = cvm_ip
        print ("iperf server: %s" % cvm_ip)
        try:
            server_cmd = ["/usr/bin/iperf", "-s"]
            if opts.verbose:
                print ("server_cmd: %s" % server_cmd)
            server_proc = multiprocessing.Process(target=run_iperf,
                                                  args=(server_cmd, server, opts.verbose))
            server_proc.start()
        except OSError as e:
            e.action = "spawning server process"
            text = "Error'd at %s: %s" % (e.action, e)
            sys.exit(text)

        client_jobs = []
        for cvm_ip in cvm_list:        
            if cvm_ip == server:
                continue
            print ("iperf client: %s" % cvm_ip)
            try:        
                client_cmd = ["/usr/bin/iperf", "-c", server, "-t", "60"]
                if opts.verbose:
                    print ("client_cmd: %s" % client_cmd)
                client_proc = multiprocessing.Process(target=run_iperf,
                                                      args=(client_cmd, cvm_ip, opts.verbose))
                client_proc.start()
                client_proc.join() # Wait for this client to finish before starting the next
                if opts.verbose:
                    print ('%s.exitcode = %s' % (client_proc.name, client_proc.exitcode))
            except OSError as e:
                e.action = "spawning client process"
                text = "Error'd at %s: %s" % (e.action, e)
                sys.exit(text)

        server_proc.terminate()
        server_proc.join()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        text = str(e)
        sys.exit(text)
