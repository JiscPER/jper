"""
Blueprint for providing reports UI
"""

import os

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
    reportsdir = app.config.get('REPORTSDIR','/home/mark/jper_reports')
    try:
        fls = os.listdir(reportsdir)
        reports = [fl for fl in fls if not fl.endswith('.cfg')]
    except:
      reports = []
    if len(reports) == 0: flash('There are currently no reports available','info')
    return render_template('reports/index.html', reports=reports)

@blueprint.route('/<filename>')
def serve(filename):
    reportsdir = app.config.get('REPORTSDIR','/home/mark/jper_reports')
    return send_from_directory(reportsdir, filename)
