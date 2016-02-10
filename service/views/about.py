'''
Created on 18 Nov 2015

Webpage - Graphic User Interface for About information

@author: Ruben Romartinez
'''

from flask import Blueprint, request, url_for, flash, redirect, make_response
from flask import render_template, abort
from flask.ext.login import login_user, logout_user, current_user

blueprint = Blueprint('about', __name__)

@blueprint.route('/')
def index():
    '''
    '''
    return render_template('about/about.html', name='About')
