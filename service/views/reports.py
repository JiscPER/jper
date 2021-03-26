"""
Blueprint for providing reports UI
"""

import os, time, re

from flask import Blueprint, request, url_for, render_template, redirect, send_from_directory, flash
from flask_login import current_user

from service import reports
from octopus.core import app

blueprint = Blueprint('reports', __name__)


@blueprint.before_request
def restrict():
    if current_user.is_anonymous:
        return redirect('/account/login')
    elif not current_user.has_role('admin'):
        return redirect(request.path.rsplit('/',1)[0] + '/login')


@blueprint.route('/')
def index():
    reportsdir = app.config.get('REPORTSDIR','/home/green/jper_reports')
    tyear = int(time.strftime('%Y'))
    try:
        #fls = os.listdir(reportsdir)
        # 2018-11-20 TD : adding time stamp of last modification date to file list
        # 2019-10-10 TD : adding line numbers (basically #records, since we have .csv)
        # 2019-11-04 TD : adding year-month string from filename to file list
        fls = [] 
        for f in sorted(os.listdir(reportsdir)):
            # 2019-10-10 TD : count the lines of .csv files
            # see: https://stackoverflow.com/questions/845058/how-to-get-line-count-cheaply-in-python#1019572
            fname = os.path.join(reportsdir,f)
            lns = sum(1 for line in open(fname))
            a = os.stat(fname)
            # 2019-11-04 TD : extract date string '%Y-%m' (i.e. YYYY-mm) from file name (in f !)
            yrm = re.findall(r'[12][0-9]{3}-[01][0-9]', f)
            yrm.append('1900-00')
            # a = os.stat(os.path.join(reportsdir,f))
            # fls.append( (f, time.ctime(a.st_mtime)) )
            fls.append( (f, time.strftime( '%F (%a) %T', time.localtime(a.st_mtime) ), lns, yrm[0]) )
        overall = [(fl,mt,nl,ym) for (fl,mt,nl,ym) in fls if not fl.endswith('.cfg') and fl.startswith('monthly')]
        details = [(fl,mt,nl,ym) for (fl,mt,nl,ym) in fls if not fl.endswith('.cfg') and fl.startswith('detailed') and int(ym.split('-')[0]) == tyear]
        if len(details) == 0:
            for tmth in range(1,13):
                fstem = "%04d-%02d.csv" % (tyear,tmth)
                open(os.path.join(reportsdir,"detailed_routed_notifications_"+fstem), 'w').close()
                open(os.path.join(reportsdir,"detailed_failed_notifications_"+fstem), 'w').close()
            flash("Empty files for year {y} generated".format(y=tyear),'info')
            return redirect(url_for('.index'))
    except Exception as e:
        overall = []
        details = []
    if len(overall) == 0 and len(details) == 0:
        flash('There are currently no reports available','info')
    return render_template('reports/index.html', detailedlists=details, grandtotals=overall)


@blueprint.route('/<filename>')
def serve(filename):
    reportsdir = app.config.get('REPORTSDIR','/home/green/jper_reports')
    return send_from_directory(reportsdir, filename)


# 2019-11-05 TD : parametrise route with a year and month (e.g. '2019-03' as yearmonth) 
@blueprint.route('/update/<yearmonth>')
def refresh(yearmonth):
    reportsdir = app.config.get('REPORTSDIR','/home/green/jper_reports')
    try:
        # flash('Updating reports, please be patient','info')
        # reports.admin_[routed|failed]_reports(frm_date,to_date,fname)
        #year = int(time.strftime('%Y'))
        #tmth = int(month)
        st = time.strptime(yearmonth,'%Y-%m')
        year = int(st.tm_year)
        tmth = int(st.tm_mon)
        ##for tmth in xrange(1,13):
        if 0 < tmth and tmth < 13 and 1900 < year:
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
        flash("Updating process encountered an error: {x}".format(x=str(e)),"error")
        time.sleep(4)

    return redirect(url_for('.index'))
