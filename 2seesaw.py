from proc_events.pec import pec_loop
import subprocess
import socket
import datetime as dt
import shlex
import traceback
import re
import os 
import socket, fcntl, struct

def get_local_ip(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    inet = fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))
    ret = socket.inet_ntoa(inet[20:24])
    return ret
#    print get_local_ip("eth0") 


#get today now.time by zhangleird
now_time=dt.datetime.now().strftime('%F %T')
white_list = ['192.168.204.5']
def check_for_reversed_shell(lsof):
    '''
    if the process was bash which had got remote socket and not got tty, then it must be a reversed shell.
    :param lsof:
    :return: positive: bool
             peer: str remote socket
    '''
    fds = [x.strip() for x in lsof.split('\n') if x]
    is_bash = has_socket = has_tty = False
    peer = pwd = None
    for fd in fds:
        detail = fd.split()
        fd = detail[3]
        t = detail[4]
        if t == 'CHR' and re.findall('(tty|pts|ptmx)', detail[-1]):
            has_tty = True
        elif 'IP' in t and detail[-1] == '(ESTABLISHED)':
            has_socket = True
            peer = detail[-2].split('->')[1]
        elif 'txt' in fd and re.findall('bash', detail[-1]):
            is_bash = True
        elif 'cwd' in fd:
            pwd = detail[-1]
    if peer:
        for ip in white_list:
            if peer.startswith(ip+':'):
                return False, None, None
    return (is_bash and has_socket and not has_tty), peer, pwd

def deal(pid):
    # simple and efficient kill

    print('###victim ip:'+get_local_ip('eth0')+'###')
#   os.system('echo reverse shell pid:%s' % (pid,))
    print('###intrude time:'+now_time+' ###')

if __name__ == "__main__":
    self_pids = []
    for e in pec_loop():
        if e['what'] == 'PROC_EVENT_EXEC':
            try:
                #exclude lsof processes
                if e['process_tgid'] in self_pids:
                    self_pids.remove(e['process_tgid'])
                    continue
                else:
                    p = subprocess.Popen(shlex.split('lsof -p %s -Pn' % (e['process_tgid'])), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    # prevent self-excitation
                    self_pids.append(int(p.pid))
                    out, err = p.communicate()
                    if out:
                        try:
                            positive, peer, pwd = check_for_reversed_shell(out)
                            if positive:
                                deal(e['process_tgid'])
                                print('###\n### Reversed Shell Detached ###\n'
                               	      '### reverse shell pid:%s ###\n'
				      '### peer intruder ip and port:%s ###\n'
                                      '### webshell directory: %s ###\n'
                                      '### system has been intruded, please Kill system process immediately. ###\n######'% (e['process_tgid'], peer, pwd))
		    	except Exception as ex:
                            traceback.print_exc(ex)
            except Exception as ex:
                traceback.print_exc(ex)
