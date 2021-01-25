from standalone_octopus.modules.es import dao
from datetime import datetime
from standalone_octopus.modules.account.exceptions import NonUniqueAccountException

def query_filter(q):
    """Function used by the query endpoint to ensure only the relevant account data is returned"""
    # q is an esprit.models.Query object

    # this limits the query to certain fields in the source, so that things like password
    # hashes and activation/reset tokens are never sent to the client
    q.include_source(["id", "email", "created_date", "last_updated", "role"])

class BasicAccountDAO(dao.ESDAO):
    __type__ = 'account'

    @classmethod
    def pull_by_email(cls, email):
        q = AccountQuery(email=email)
        accs = cls.object_query(q=q.query())
        if len(accs) > 1:
            raise NonUniqueAccountException("There is more than one user account with the email {x}".format(x=email))
        elif len(accs) == 1:
            return accs[0]
        else:
            return None

    @classmethod
    def get_by_reset_token(cls, reset_token, not_expired=True):
        q = AccountQuery(reset_token=reset_token)
        accs = cls.object_query(q=q.query())
        if len(accs) > 1:
            raise NonUniqueAccountException("There is more than one user account with the reset token {x}".format(x=reset_token))
        elif len(accs) == 0:
            return None

        acc = accs[0]
        if acc.is_reset_expired() and not_expired:
            return None
        return acc

    @classmethod
    def get_by_activation_token(cls, activation_token, not_expired=True):
        q = AccountQuery(activation_token=activation_token)
        accs = cls.object_query(q=q.query())
        if len(accs) > 1:
            raise NonUniqueAccountException("There is more than one user account with the activation token {x}".format(x=activation_token))
        elif len(accs) == 0:
            return None

        acc = accs[0]
        if acc.is_activation_expired() and not_expired:
            return None
        return acc


class AccountQuery(object):
    def __init__(self, email=None, reset_token=None, activation_token=None):
        self.email = email
        self.reset_token = reset_token
        self.activation_token = activation_token

    def query(self):
        q = {
            "query" : {
                "bool" : {
                    "must" : []
                }
            }
        }
        if self.email is not None:
            q["query"]["bool"]["must"].append({"term" : {"email.exact" : self.email}})
        if self.reset_token is not None:
            q["query"]["bool"]["must"].append({"term" : {"reset_token.exact" : self.reset_token}})
        if self.activation_token is not None:
            q["query"]["bool"]["must"].append({"term" : {"activation_token.exact" : self.activation_token}})

        return q