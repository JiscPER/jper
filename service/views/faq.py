"""
Blueprint for FAQ page
"""

import os

from flask import Blueprint, request, render_template, redirect, send_from_directory, flash
from flask.ext.login import current_user

from octopus.core import app

blueprint = Blueprint('reports', __name__)

@blueprint.route('/')
def faq():
    '''
    '''
    return render_template('faq/faq.html', faq=faq)
    
    
