# If you are going to use the account module, you need to add the DAO to the ES
# mappings with
#
#ELASTIC_SEARCH_MAPPINGS = [
#  octopus.modules.account.dao.BasicAccountDAO
#]
#
# To use the command line scripts, ensure that the following is configured in the CLI_SCRIPTS config:
#
# CLI_SCRIPTS = {
#    "usermod" : "octopus.modules.account.scripts.UserMod"
#}

# enbale the account module at all - setting this to True will cause the setup script to run
ACCOUNT_ENABLE = False

# make this something secret in your overriding local.cfg
SECRET_KEY = "default-key"

# role which denotes a super user
ACCOUNT_SUPER_USER_ROLE = "admin"

# Model object (must extend from BasicAccount) for managing user accounts
ACCOUNT_MODEL = "octopus.modules.account.models.BasicAccount"

# whether the UI for listing users should be available, and to which user role
ACCOUNT_LIST_USERS = False
ACCOUNT_LIST_USERS_ROLE = "list_users"

# if user listing is enabled, this points to the query endpoint where the data can be retrieved
CLIENTJS_ACCOUNT_LIST_ENDPOINT = "/account_query/account"

# You will also need to specify the query route as follows
# QUERY_ROUTE = {
#     "account_query" : {
#         "account" : {
#             "auth" : True,
#             "role" : "list-users",
#             "filters" : [
#                  "octopus.modules.account.dao.query_filter"
#              ],
#             "dao" : "octopus.modules.account.dao.BasicAccountDAO"
#         }
#     }
# }
# and you will also need to setup your query endpoint at those paths

# the user role which allows a user to edit other user accounts
ACCOUNT_EDIT_USERS_ROLE = "edit_users"

# the user role which allows a user to create a new user
ACCOUNT_CREATE_USER_ROLE = "create_users"

# should unregsitered/unauthenticated people be allowed to hit the registration page
ACCOUNT_ALLOW_REGISTER = False

# UI Form Contexts for the various interface aspects
ACCOUNT_LOGIN_FORM_CONTEXT = "octopus.modules.account.forms.LoginFormContext"
ACCOUNT_USER_FORM_CONTEXT = "octopus.modules.account.forms.BasicUserFormContext"
ACCOUNT_FORGOT_FORM_CONTEXT = "octopus.modules.account.forms.ForgotFormContext"
ACCOUNT_RESET_FORM_CONTEXT = "octopus.modules.account.forms.ResetFormContext"
ACCOUNT_REGISTER_FORM_CONTEXT = "octopus.modules.account.forms.BasicRegisterFormContext"
ACCOUNT_ACTIVATE_FORM_CONTEXT = "octopus.modules.account.forms.ActivateFormContext"

# where to direct the user after login if they haven't already got a page in their "next" location
ACCOUNT_LOGIN_REDIRECT_ROUTE = "index"

# URL routing (suitable for passing to url_for) to redirect the user to on logout
ACCOUNT_LOGOUT_REDIRECT_ROUTE = "index"

# where to direct the user once they have submitted a forgotten password request
ACCOUNT_FORGOT_REDIRECT_ROUTE = "account.forgot_pending"

# where to direct the user once they have created a user account
ACCOUNT_REGISTER_REDIECT_ROUTE = "account.index"

# amount of time a reset token is valid for (86400 is 24 hours)
ACCOUNT_RESET_TIMEOUT = 86400
ACCOUNT_ACTIVATE_TIMEOUT = ACCOUNT_RESET_TIMEOUT * 14

ACCOUNT_RESET_EMAIL_SUBJECT = "Password reset"
ACCOUNT_ACTIVATE_EMAIL_SUBJECT = "Activate your account"

# Default roles to create your users with
ACCOUNT_DEFAULT_ROLES = []