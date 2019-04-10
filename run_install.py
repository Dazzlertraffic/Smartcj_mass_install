#!/usr/bin/python3.7
# -*- coding: utf-8 -*-
import os
import subprocess
import shutil
import time
from config import base_dir, pass_to_scj, excluded_domain, mysql_host, mysql_user, mysql_pass, public_html, admin_email, \
    prefix_to_folder, prefix_to_db, included_domain


class Domain:
    def __init__(self, name):
        self.name = name
        self.script_folder = prefix_to_folder + name[:-4]
        self.admin_email = admin_email
        self.mysql_name = prefix_to_db + self.name[:-4]
        if public_html:
            self.dir_to_domain = base_dir + '/' + self.name + '/public_html/'
        else:
            self.dir_to_domain = base_dir + '/' + self.name + '/'

        self.dir_to_folder = self.dir_to_domain + self.script_folder + '/'
        self.dir_to_admin_folder = self.dir_to_folder + 'admin/'
        self.dir_to_cgi = self.dir_to_folder + 'cgi/'
        self.admin_url = 'http://' + self.name + '/' + self.script_folder + '/admin/'

    def create_db(self):
        subprocess.call(
            'mysql -e "create database ' + self.mysql_name + ' DEFAULT CHARACTER SET utf8 '
                                                             'DEFAULT COLLATE utf8_general_ci;"',
            shell=True)
        print(f"DB {self.mysql_name} create!")

    def check_folder(self):
        return os.path.isdir(self.dir_to_folder)

    def check_mysql(self):
        command = 'mysql -e "select schema_name from information_schema.schemata where schema_name = \'' + self.mysql_name + '\';"'
        response = subprocess.check_output(command, shell=True)
        if response != b'':
            return True

    def install_script(self):
        os.chdir(self.dir_to_domain)
        com = 'curl -sS http://smartcj.com/updates2/install | php -- mysql_host=' + mysql_host + ' mysql_user=' + \
              mysql_user + ' mysql_pass=' + mysql_pass + ' mysql_name=' + self.mysql_name + ' scj_folder=' + \
              self.script_folder + ' domain=' + self.name + ' admin_email=' + self.admin_email
        time.sleep(3)
        back_code = subprocess.Popen(com, stdout=subprocess.PIPE, stderr=None, shell=True)
        try:
            output = back_code.communicate(timeout=30)
            message = output[0].decode("utf-8")
            ok_message = message.find("Done, everything's ok")
            if int(ok_message) > 0:
                print(f"{self.name} - successfully")
            else:
                print(f"{self.name} - bad installition! Check log...")
        except:
            print(self.name, 'Timeout expired! Check log...')
            back_code.kill()
            message = 'Timeout Error;PID:' + str(back_code.pid)

        write_log(info=message, file_to_write='install_script.log')

    def change_password(self):
        comand = 'htpasswd -bc ' + self.dir_to_admin_folder + '.htpasswd admin ' + pass_to_scj
        subprocess.Popen(comand, stdout=subprocess.PIPE, stderr=None, shell=True)
        print(f"{self.name} - Password change")

    def copy_system_file(self):
        file_index = 'index.php'
        file_common = 'common.php'
        shutil.copyfile(self.dir_to_cgi + file_index, self.dir_to_domain + file_index)
        shutil.copyfile(self.dir_to_cgi + file_common, self.dir_to_domain + file_common)
        print(f"{self.name} - {file_index} and {file_common} were copied")

    def create_log(self):
        with open(admin_dir + '/file/' + '/admin_info.cvs', mode='a+', encoding='utf-8') as admin_file:
            line = self.admin_url + '|' + pass_to_scj + '\n'
            admin_file.write(line)

    def create_sh_file(self):
        with open(admin_dir + '/file/' + 'rotation.sh', mode='a+', encoding='utf-8') as cron_file:
            line = 'cd ' + self.dir_to_folder + 'bin; env HTTP_HOST=' + self.name + ' /usr/bin/php -q rotation.php &' + '\n'
            cron_file.write(line)

        with open(admin_dir + '/file/' + 'cron.sh', mode='a+', encoding='utf-8') as cron_file:
            line = 'cd ' + self.dir_to_folder + 'bin; env HTTP_HOST=' + self.name + ' /usr/bin/php -q cron.php &' + '\n'
            cron_file.write(line)

        print(f"{self.name} - cron add!")


def write_log(info, file_to_write):
    with open(file_to_write, encoding='UTF-8', mode='w') as file:
        file.write(info)


def start_install():
    print(f"{'*':*^60}")
    print(f"{'Welcome to auto installer TCMS':*^60}")
    print(f"{'*':*^60}")
    folders = os.listdir(path=base_dir)
    domains = []
    for folder in folders:
        if len(included_domain) > 0:
            if os.path.isdir(base_dir + '/' + folder) and folder in included_domain:
                site = Domain(name=folder)
                domains.append(site)
        elif os.path.isdir(base_dir + '/' + folder) and folder not in excluded_domain:
            site = Domain(name=folder)
            domains.append(site)

    print('Installition in domais:')
    for domain in domains:
        print(domain.name)
    print('If ok print - yes')
    answer = input()
    if answer != 'yes':
        return exit()

    print('Check directories and databases')
    for domain in domains:
        if domain.check_folder():
            print('Folder', domain.script_folder, 'alredy exist... please check and try again')
            break
        elif domain.check_mysql():
            print('Database', domain.mysql_name, 'alredy exist... please check and try again')
            break
    else:
        print('All Ok...')
        os.mkdir(admin_dir + '/file', mode=0o777)
        for domain in domains:
            print(f"{'Install ' + domain.name:*^60}")
            time.sleep(1)
            domain.create_db()
            time.sleep(1)
            domain.install_script()
            time.sleep(3)
            domain.copy_system_file()
            time.sleep(3)
            domain.change_password()
            time.sleep(3)
            domain.create_log()
            time.sleep(3)
            domain.create_sh_file()
            time.sleep(3)


if __name__ == "__main__":
    admin_dir = os.getcwd()
    start_install()
