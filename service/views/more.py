'''
Created on 18 Nov 2015

Webpage - Graphic User Interface for more information

@author: Ruben Romartinez
'''

from flask import Blueprint
from flask import render_template

blueprint = Blueprint('more', __name__)


@blueprint.route('/institutions/', methods=['GET','POST'])
def institutions():
    '''
    '''
    return render_template('more/institutions.html', name='Information about Institutions')

@blueprint.route('/publishers/', methods=['GET','POST'])
def publishers():
    '''
    '''
    return render_template('more/publishers.html', name='Information about Publishers')

@blueprint.route('/resources/', methods=['GET','POST'])
def resources():
    '''
    '''        
    return render_template('more/resources.html', name="Resources")

@blueprint.route('/jisc/', methods=['GET','POST'])
def deepgreen():
    '''
    '''
    return render_template ('more/jisc.html', name="About DeepGreen")

