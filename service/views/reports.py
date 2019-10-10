"""
Blueprint for providing reports UI
"""

import os, time

from flask import Blueprint, request, render_template, redirect, send_from_directory, flash
from flask.ext.login import current_user

from octopus.core import app

blueprint = Blueprint('reports', __name__)


@blueprint.before_request
def restrict():
    if current_user.is_anonymous():
        return redirect('/account/login')
    elif not current_user.has_role('admin'):
        return redirect(request.path.rsplit('/',1)[0] + '/login')


@blueprint.route('/')
def index():
    reportsdir = app.config.get('REPORTSDIR','/home/green/jper_reports')
    try:
        #fls = os.listdir(reportsdir)
        # 2018-11-20 TD : adding time stamp of last modification date to file list
        fls = [] 
        for f in sorted(os.listdir(reportsdir)):
            a = os.stat(os.path.join(reportsdir,f))
            # fls.append( (f, time.ctime(a.st_mtime)) )
            fls.append( (f, time.strftime('%F (%a) %T',time.localtime(a.st_mtime))) )

        overall = [(fl,mt) for (fl,mt) in fls if not fl.endswith('.cfg') and fl.startswith('monthly')]
        details = [(fl,mt) for (fl,mt) in fls if not fl.endswith('.cfg') and fl.startswith('detailed')]
    except:
        overall = []
        details = []
    if len(overall) == 0 and len(details) == 0:
        flash('There are currently no reports available','info')
    return render_template('reports/index.html', detailedlists=details, grandtotals=overall)


@blueprint.route('/<filename>')
def serve(filename):
    reportsdir = app.config.get('REPORTSDIR','/home/green/jper_reports')
    return send_from_directory(reportsdir, filename)


@blueprint.route('/update')
def refresh():
    reportsdir = app.config.get('REPORTSDIR','/home/green/jper_reports')
    flash('Updating reports, please be patient.','info')
    # admin_[routed|failed]_reports(frm_date,to_date,fname)
    return index()
