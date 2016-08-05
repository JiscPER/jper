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

@blueprint.route('/institutions/', methods=['GET','POST'])
def institutions():
    '''
    '''
    return render_template('about/institutions.html', name='Information for Institutions')

@blueprint.route('/publishers/', methods=['GET','POST'])
def publishers():
    '''
    '''
    return render_template('about/publishers.html', name='Information for Publishers')

@blueprint.route('/resources/', methods=['GET','POST'])
def resources():
    '''
    '''        
    return render_template('about/resources.html', name="Technical documentation")
    
@blueprint.route('/deepgreen/', methods=['GET','POST'])
def deepgreen():
    '''
    '''
    return render_template ('about/deepgreen.html', name="About DeepGreen")
    
@blueprint.route('/jisc/', methods=['GET','POST'])
def jisc():
    '''
    '''
    return render_template ('about/jisc.html', name="About JISC")
