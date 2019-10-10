"""
Blueprint for providing reports UI
"""

import os, time

from flask import Blueprint, request, render_template, redirect, send_from_directory, flash
from flask.ext.login import current_user

from service import reports
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
        # 2019-10-10 TD : adding line numbers (basically #records, since we have .csv)
        fls = [] 
        for f in sorted(os.listdir(reportsdir)):
            # 2019-10-10 TD : count the lines of .csv files
            # see: https://stackoverflow.com/questions/845058/how-to-get-line-count-cheaply-in-python#1019572
            lns = sum(1 for line in open(f))
            a = os.stat(os.path.join(reportsdir,f))
            # fls.append( (f, time.ctime(a.st_mtime)) )
            fls.append( (f, time.strftime('%F (%a) %T',time.localtime(a.st_mtime)), lns) )

        overall = [(fl,mt,nl) for (fl,mt,nl) in fls if not fl.endswith('.cfg') and fl.startswith('monthly')]
        details = [(fl,mt,nl) for (fl,mt,nl) in fls if not fl.endswith('.cfg') and fl.startswith('detailed')]
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
    try:
        flash('Updating reports, please be patient.','info')
        # reports.admin_[routed|failed]_reports(frm_date,to_date,fname)
        year = int(time.strftime('%Y'))
        for tmth in xrange(1,13):
            nxmth = (tmth+1) % 13
            frm_date = "%04d-%02d-01T00:00:00Z" % (year,tmth)
            fstem = "%04d-%02d.csv" % (year,tmth)
            if nxmth == 0:
                year = year + 1
                nxmth = 1
            to_date = "%04d-%02d-01T00:00:00Z" % (year,nxmth)
            #
            reports.admin_routed_report(frm_date, to_date, reportsdir + "/detailed_routed_notifications_" + fstem)
            reports.admin_failed_report(frm_date, to_date, reportsdir + "/detailed_failed_notifications_" + fstem)

    except Exception as e:
        flash("Updating process encountered an error: {x}".format(x=e.message),"error")
        time.sleep(4)

    return redirect('/')
