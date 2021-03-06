#!/usr/bin/env python
#coding=utf8

from flask import request,render_template,session,redirect
from . import app
from common_func import session_check,role_check
from datetime import *
import json
from utils import woops_log,mysql_exec

def server_list():
	select_fields = ['PrivateIP']
        svr_list = [x[0] for x in mysql_exec.select_sql('serverinfo',select_fields)]
        woops_log.log_write('server').debug('server_list:%s' % svr_list)
	return svr_list

@app.route("/cmdb/server_add",methods=['GET','POST'])
@session_check
@role_check
def server_add():
        if request.method == 'GET':
                return render_template("server_add.html")
        if request.method == 'POST':
                server_add_dict = dict((i,j[0]) for i,j in dict(request.form).items())
                if not server_add_dict['HostName'].strip() or not server_add_dict['ENV'].strip() or not server_add_dict['PrivateIP']:
                        woops_log.log_write('server').error('The * symbol part of the input cannot be empty')
                        msg = "The * symbol part of the input cannot be empty"
                        return json.dumps({'result':1,'msg':msg})
                if not server_add_dict['OS'] or not server_add_dict['Kernel'] or not server_add_dict['CpuType']:
                        woops_log.log_write('server').error('The * symbol part of the input cannot be empty')
                        msg = "The * symbol part of the input cannot be empty"
                        return json.dumps({'result':1,'msg':msg})
                if not server_add_dict['CpuCount'] or not server_add_dict['RAM_GB'] or not server_add_dict['PhyDiskSize'] or not server_add_dict['IDC']:
                        woops_log.log_write('server').error('The * symbol part of the input cannot be empty')
                        msg = "The * symbol part of the input cannot be empty"
                        return json.dumps({'result':1,'msg':msg})
		if server_add_dict['PrivateIP'] in server_list():
			woops_log.log_write('server').error('IP "%s" already exists' % server_add_dict['PrivateIP'])
			return json.dumps({'result':1,'msg':'IP already exists'})
                server_add_dict['OnlineTime'] = datetime.now().strftime("%Y-%m-%d %X")
                woops_log.log_write('server').debug('server_add_dict: %s' % server_add_dict)
                insert_fields = [x for x in server_add_dict.keys()]
                mysql_exec.insert_sql('serverinfo',insert_fields,server_add_dict)
                woops_log.log_write('server').info('The server "%s" added successfully' % server_add_dict['PrivateIP'])
                return json.dumps({'result':0,'msg':'ok'})

## 在修改 服务器 状态时 先查询这个 IP 是否在 cmdb 中使用,如果在使用则禁止修改该状态 ##
def app_ip_detail(mysql_table):
        app_ip_fields = ['app_ip']
        app_ip_select = mysql_exec.select_sql('%s' %(mysql_table),app_ip_fields)
        if app_ip_select:
                app_ip_list_pre = [i[0].split(' ; ') for i in app_ip_select]
                app_ip_list = []
                for i in app_ip_list_pre:
                        app_ip_list = app_ip_list + i
                app_ip_list = list(set(app_ip_list))
                woops_log.log_write('server').debug('app_ip_list: %s' % app_ip_list)
                return app_ip_list

@app.route("/cmdb/server_update",methods=['GET','POST'])
@session_check
def server_update():
        if request.method == 'GET':
                select_condition = {}
                select_condition['id'] = request.args.get('id')
                fields_1 = ['id','HostName','PrivateIP','PublicIP','ENV','ServerBrand','ServerModel','OS','Kernel']
                fields_2 = ['CpuType','CpuCount','RAM_GB','PhyDiskSize','IDC','status','OnlineTime','OfflineTime']
                fields = fields_1 + fields_2
                server_info = mysql_exec.select_sql('serverinfo',fields,select_condition)
                server_info_dict = [dict(zip(fields,i)) for i in server_info][0]
                woops_log.log_write('server').debug('server_info_dict: %s' % server_info_dict)
                return json.dumps(server_info_dict)
        if request.method == 'POST':
                server_update_dict = dict((i,j[0]) for i,j in dict(request.form).items())
                if not server_update_dict['HostName'].strip() or not server_update_dict['ENV'].strip() or not server_update_dict['OS']:
                        woops_log.log_write('server').error('The * symbol part of the input cannot be empty')
                        msg = "The * symbol part of the input cannot be empty"
                        return json.dumps({'result':1,'msg':msg})
                if  not server_update_dict['Kernel'] or not server_update_dict['CpuType'] or not server_update_dict['CpuCount']:
                        woops_log.log_write('server').error('The * symbol part of the input cannot be empty')
                        msg = "The * symbol part of the input cannot be empty"
                        return json.dumps({'result':1,'msg':msg})
                if not server_update_dict['RAM_GB'] or not server_update_dict['PhyDiskSize'] or not server_update_dict['IDC']:
                        woops_log.log_write('server').error('The * symbol part of the input cannot be empty')
                        msg = "The * symbol part of the input cannot be empty"
                        return json.dumps({'result':1,'msg':msg})
                if server_update_dict['status'] == '1' or server_update_dict['ENV'] != 'online':
                        app_ip_list = app_ip_detail('cmdb_online')
                        if server_update_dict['PrivateIP'] in app_ip_list:
                                woops_log.log_write('server').error('Server update failure,because of he ip has been in cmdb_online ; Please delete if from cmdb_online first!')
                                msg = 'The ip has been in cmdb_online ; Please delete if from cmdb_online first!'
                                return json.dumps({'result':1,'msg':msg})

                update_conditions = {}
                update_conditions['id'] = server_update_dict['id'].strip('')
                update_conditions['PrivateIP'] = server_update_dict['PrivateIP'].strip('')
                if server_update_dict['status'].strip('') == '1':
                        server_update_dict['OfflineTime'] = datetime.now().strftime("%Y-%m-%d %X")
                else:
                        server_update_dict['OfflineTime'] = ''
                woops_log.log_write('server').debug('server_update_dict: %s' % server_update_dict)
                del server_update_dict['id']
                del server_update_dict['PrivateIP']
                mysql_exec.update_sql('serverinfo',server_update_dict,update_conditions)
                woops_log.log_write('server').info('The server "%s" update successfully' % update_conditions['PrivateIP'])
                return json.dumps({'result':0,'msg':'ok'})

@app.route("/cmdb/server_list",methods=['GET'])
@session_check
def server_list():
        fields_1 = ['id','HostName','PrivateIP','PublicIP','ENV','OS','Kernel']
        fields_2 = ['CpuCount','RAM_GB','PhyDiskSize','IDC','status']
        fields = fields_1 + fields_2
        server_list = mysql_exec.select_sql('serverinfo',fields)
        server_list_list = [dict(zip(fields,i)) for i in server_list]
        woops_log.log_write('server').debug('server_list_list: %s' % server_list_list)
        return render_template("server_list.html",server_list=server_list_list)

@app.route("/cmdb/server_delete",methods=["GET"])
@session_check
def server_delete():
        delete_condition = {}
        delete_server = {}
        delete_condition['id'] = request.args.get('id')
        delete_server = [dict(zip(['PrivateIP'],i)) for i in mysql_exec.select_sql('serverinfo',['PrivateIP'],delete_condition)][0]
        mysql_exec.delete_sql('serverinfo',delete_condition)
        woops_log.log_write('server').info('Delete server "%s" success' % delete_server)
        return json.dumps({'result':0,'msg':'ok'})

