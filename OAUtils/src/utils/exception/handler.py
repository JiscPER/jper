'''
Created on 26 Oct 2015

@author: Ruben.Alonso

@Description: Module created to manage all different errors and exceptions.

'''
import utils.logger.handler as LH


class Error(Exception):

    """Base class for exceptions in this module."""
    pass


class InputError(Error):
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
        error -- actual error information
    """

    def __init__(self, message="Incorrect input exception", error=""):
        LH.logger.error(str(message) + ". " + str(error))
        self.error = error
        self.message = message


class IncorrectFormatError(Error):
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
        error -- actual error information
    """

    def __init__(self, message="Incorrect format exception", error=""):
        LH.logger.error(str(message) + ". " + str(error))
        self.error = error
        self.message = message


class DBConnectionError(Error):
    """Exception raised for errors in the input.

    Attributes:
        message -- explanation of the error
        error -- actual error information
    """

    def __init__(self, message="DB connection exception", error=""):
        LH.logger.error(str(message) + ". " + str(error))
        self.error = error
        self.message = message


class GenericError(Error):
    """Exception raised for generic errors.

    Attributes:
        message -- explanation of the error
        error -- actual error information
    """

    def __init__(self, message="Generic exception", error=""):
        LH.logger.error(str(message) + ". " + str(error))
        self.error = error
        self.message = message


class DeleteDocException(Error):
    """Exception raised when we have errors deleteing documents from DB.

    Attributes:
        message -- explanation of the error
        error -- actual error information
    """

    def __init__(self, message="DeleteDoc exception", error=""):
        LH.logger.error(str(message) + ". " + str(error))
        self.error = error
        self.message = message
